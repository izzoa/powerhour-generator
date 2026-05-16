## Context

The PowerHour GUI shells out to `yt-dlp` (located via `shutil.which`) to download playlists. yt-dlp is the project's most version-sensitive dependency because YouTube changes extractors frequently — an outdated yt-dlp produces extractor errors that surface in the GUI as a generic "Failed to download playlist" with no actionable path forward.

Today the project:

- Declares a floor pin of `yt-dlp>=2023.1.1` in `setup.py` and `requirements-dev.txt`. This floor is now ~3 years stale and effectively unconstrained.
- Does not install yt-dlp through `requirements.txt` or `environment.yml` (commented out).
- Provides three OS-specific install scripts (`brew install yt-dlp` on macOS, `sudo python3 -m pip install yt-dlp` on Debian, `choco install yt-dlp` on Windows), all unpinned.
- Does not bundle yt-dlp into the PyInstaller build (`powerhour.spec`).
- Has no in-app surface for yt-dlp version, freshness, or update.

The existing GUI module is `powerhour/powerhour_gui.py` (~2500 lines). Threaded work flows through a `queue.Queue` consumed by `PowerHourGUI.process_queue()` (polled every 100ms via `self.after(100, self.process_queue)`), with message types `progress`, `status`, `log`, `video_progress`, `complete`, `error`. The Output Log panel (`ScrolledText` at `powerhour_gui.py:627`) renders color-tagged log messages routed through that queue.

**Crucially, a status bar already exists.** `PowerHourGUI.build_status_bar()` at `powerhour_gui.py:457` is called from `__init__` at `powerhour_gui.py:179`, grids `self.status_bar` at `row=4`, and packs three labels: `hint_label` (left), `operation_label` (left/center), `resource_label` (right). A 2-second resource-usage poller (`update_resource_usage()`) writes into `resource_label`. The existing `error` message-type handler at `powerhour_gui.py:1439-1451` is destructive: it shows a "Processing Error" dialog, sets status to "Error", calls `reset_ui_state()`, and calls `cleanup_temp_files()`. Any code path that emits the generic `error` message inherits all of that behavior.

## Goals / Non-Goals

**Goals:**

- Show the installed yt-dlp version somewhere persistent in the GUI.
- Tell the user, on launch, whether their yt-dlp is current (against PyPI's latest stable).
- Provide a single in-app action that performs the *correct* upgrade for their install method, or shows a manual command when the install method is unsupported by auto-upgrade.
- Surface the actual output of the upgrade command in the existing log panel.
- Keep the Tk main loop responsive throughout (no blocking network or subprocess on the UI thread).
- Degrade gracefully on no-network, no-yt-dlp, or unsupported install methods.
- Preserve existing status-bar behavior (hint, operation, resource labels) and the 2-second resource poller.

**Non-Goals:**

- Auto-updating yt-dlp at launch (user agency over package state is preserved).
- Bundling yt-dlp into the PyInstaller build.
- Pinning yt-dlp in `setup.py` / `requirements*.txt`.
- Supporting the yt-dlp nightly channel as a freshness source (`yt-dlp/yt-dlp-nightly-builds`). A nightly install whose version-tuple is newer than PyPI's stable returns `current` from the comparator (see decision 4) — the user sees "Up to date" and is not prompted to downgrade. Explicitly out of scope; no nightly-specific behavior is added.
- Auto-installing yt-dlp when it's missing (only update is in scope; missing state will show a passive hint with a link to install docs).
- Fixing the broader "yt-dlp failures don't reflect in the GUI" signal-loss problem in `_download_playlist` (forwarding stderr, removing the `[download]`-only filter, `--newline`, zero-files-after-exit-0). Sibling change.

## Decisions

### 1. Install-method detection: path classification with an `unsupported` outcome

**Decision:** Resolve `shutil.which('yt-dlp')`, then `os.path.realpath()` to dereference symlinks, then classify the absolute path against a small set of known prefixes/markers in a specific order. Anything that does not match a known *managed* pattern AND is not in a writable user-controlled location is classified as `unsupported` — not `standalone`.

Path normalization: before any test, paths are realpath-resolved AND on Windows, casefolded with `\\` replaced by `/`. Tests are written against the normalized form.

Classification order (first match wins; the function is never called when discovery returns `None` — `missing` is handled by the discovery layer, not by the classifier):

| # | Path test | Install method | Upgrade command |
|---|---|---|---|
| 1 | Contains `/pipx/` | `pipx` | `pipx upgrade yt-dlp` |
| 2 | Contains `/Cellar/yt-dlp/` or starts with `/opt/homebrew/` or `/usr/local/Cellar/` | `brew` | `brew upgrade yt-dlp` |
| 3 | Contains `/chocolatey/` (after Windows separator normalization) | `choco` | `choco upgrade yt-dlp -y` |
| 4 | **Path-pattern unsupported**: starts with `/nix/store/`, `/snap/`, `/var/lib/flatpak/`, `/usr/bin/`, `/usr/sbin/`, OR matches `/.pyenv/shims/`, `/.asdf/shims/`, `/.local/share/mise/shims/`, `/scoop/`, `/microsoft/winget/`, or `/lib/node_modules/` | `unsupported` | (no auto-upgrade — show per-manager copy-paste command) |
| 5 | **Filesystem-augmented unsupported (conda)**: parent directory has a sibling `conda-meta/` directory (i.e., binary is inside a conda environment) | `unsupported` | (no auto-upgrade — show conda-specific command) |
| 6 | Path contains `/site-packages/` OR shebang resolves to a Python interpreter that, when invoked with `import yt_dlp; print(yt_dlp.__file__)`, prints a path rooted in the same `site-packages` directory tree as the script — verified per decision 2 | `pip` | `<verified_owning_python> -m pip install -U yt-dlp` |
| 7 | Binary is a real executable file in a user-writable directory not matching any pattern above (e.g., `~/bin/yt-dlp`, `~/.local/bin/yt-dlp`) | `standalone` | `<binary_path> -U` (absolute path, not PATH-resolved) |

**Critical ordering rule:** Path-pattern unsupported checks (step 4) and the conda filesystem check (step 5) MUST run BEFORE pip detection (step 6). A conda env's `yt-dlp` has a shebang to a real Python interpreter that successfully imports `yt_dlp` from the env's site-packages — so without this ordering, conda envs would classify as `pip` and pass pip verification, then be reclassified to `unsupported` only by the system-managed-Python check in decision 2, losing the conda-specific manual command. Same risk for `/usr/bin/yt-dlp` on Debian. The reordering ensures the user sees the manager-specific copy-paste command for their actual install method.

**Why pipx is checked before pip:** A pipx install has a venv with a `site-packages/` directory, so the shebang and path both look pip-shaped. The `/pipx/` substring is the discriminator.

**Why the `unsupported` outcome exists:** Package managers like apt/dnf/pacman, conda, pyenv/asdf/mise shims, nix, snap, flatpak, scoop, winget, and npm all own the binary in a way we cannot safely upgrade from this app. The spec's "MUST NOT execute a generic `yt-dlp -U` for managed installs" rule (Requirement: *Run install-method-appropriate upgrade command*) requires that we positively recognize "not standalone" rather than defaulting to standalone-and-hope.

**Alternatives considered:**

- *Ask each package manager.* Run `brew list yt-dlp`, `pip show yt-dlp`, `choco list yt-dlp` and see which succeeds. Three subprocess calls on every launch is wasteful. We do, however, optionally run *one* targeted secondary check when the path-pattern result is ambiguous (e.g., `/usr/local/bin/yt-dlp` could be brew on Intel Macs or a distro install on Linux).
- *Parse `yt-dlp --version` for hints.* It returns only the version string; no install-method info.
- *Read the shebang of the resolved file.* Useful as a secondary signal for `pip` detection; we use this in step 6.

### 2. Pip-owning Python discovery: structural verification, not just version match

**Decision:** When path classification produces `pip` (or shebang-based pip detection in step 6), we identify the owning Python interpreter and verify it structurally before running an upgrade.

Discovery:

1. Read the shebang of the resolved `yt-dlp` script.
2. If the shebang is `/usr/bin/env python3`, resolve via `PATH` lookup using the env we inherited.
3. On Windows, the `yt-dlp.exe` shim sits next to a `python.exe` in `Scripts/`; walk up two directories.
4. Resolve any symlinks on the discovered interpreter path.

Structural verification (ALL must pass):

1. The discovered interpreter path exists and is executable.
2. The interpreter is not a pyenv/asdf/mise shim (those are shell scripts dispatching to real interpreters and are unsafe targets). Check by reading the file's first bytes / extension.
3. Running `<python> -c "import yt_dlp; print(yt_dlp.__file__)"` succeeds with exit code 0 AND prints a path whose directory contains the resolved `yt-dlp` script's site-packages root (i.e., the interpreter actually owns *this* `yt_dlp` install, not some other one).
4. The interpreter's `sys.executable` (printed via `<python> -c "import sys; print(sys.executable)"`) matches the discovered path after realpath.

System-Python detection (refuse auto-upgrade if any apply):

1. Discovered interpreter's `sys.prefix == sys.base_prefix` (NOT in a venv) AND its path is under `/usr/bin`, `/usr/local/bin`, `/usr/sbin`, or a Framework path on macOS.
2. The `EXTERNALLY-MANAGED` marker file exists alongside the interpreter's stdlib (PEP 668 — Debian, Fedora, modern macOS Python.org installs).
3. The interpreter's owning directory is not writable by the current user.

If any verification step fails, the install method is reclassified to `unsupported` for the click handler and the GUI presents a copy-paste command. The reclassification is logged for diagnostics.

**Rationale:** Version equality between `yt-dlp --version` and `<python> -c "import yt_dlp; print(yt_dlp.__version__)"` is necessary but not sufficient — two different installs can have the same version. Comparing module file paths confirms we're actually targeting the same install. Refusing system Python via `EXTERNALLY-MANAGED` and venv-or-not checks avoids the well-known `pip install` failure mode on modern Debian/Fedora.

**Alternatives considered:**

- *Compare versions only.* Too loose; see above.
- *Check `pip show yt-dlp -f`* against the discovered interpreter. Equivalent information, slower, requires pip to be installed in that interpreter (which is not always true for embedded/system Pythons).

### 3. Latest-version source: PyPI JSON API

**Decision:** Single GET to `https://pypi.org/pypi/yt-dlp/json`, parse JSON, read `info.version`. Use stdlib `urllib.request` with a 5-second timeout and a User-Agent of `PowerHour-Generator/<version>`. Treat HTTP errors and network errors uniformly: latest version becomes `None`, status bar shows installed version only with no freshness indicator, one info-level line written to the Output Log.

**Rationale:** PyPI publishes yt-dlp stable releases on the same cadence as GitHub. It has no per-IP rate limit comparable to GitHub's 60/hr unauthenticated cap, which matters because a NAT or campus IP launching the app on many machines per day would otherwise hit GitHub's limit. PyPI's JSON is simpler (no need to filter pre-releases — `info.version` is always the latest stable).

**Explicit scope decision:** Nightlies are out of scope. yt-dlp's nightly channel is the separate `yt-dlp/yt-dlp-nightly-builds` GitHub repository, not the main release feed. Users who installed a nightly will see PyPI's stable as "latest"; if their nightly version-tuple is newer, the comparator returns `current` (because we treat installed-newer-than-latest as up-to-date — see decision 4).

**Alternatives considered:**

- *GitHub Releases API* (`releases/latest`). Equally easy for stable. 60/hr unauthenticated rate limit per IP. Rejected primarily for the rate-limit risk on shared IPs. ETag/`If-None-Match` caching could mitigate but adds complexity for marginal benefit.
- *`yt-dlp -U --dry-run`.* yt-dlp doesn't expose a dry-run for self-update.
- *`pip index versions yt-dlp`.* Requires pip on PATH, slow, only works for pip-installed users.

### 4. Version comparison: tuple compare, unparseable → `unknown`

**Decision:** Parse both versions into tuples of integers split on `.`, padding the shorter to match length with zeros. Compare lexicographically. Strip any leading `v` (GitHub tag prefix) before splitting. Handle PyPI's normalization (`2026.03.17` → `2026.3.17`) by parsing integers (which discards leading zeros naturally).

The comparator returns one of:

- `current` — installed >= latest
- `outdated` — installed < latest
- `unknown` — either side fails to parse as an integer tuple, or either side is `None`

**The `unknown` outcome is critical.** The original draft treated unparseable input as `current`, which silently hides a broken upstream response or a non-standard version channel (e.g., a nightly build with non-date format). `unknown` surfaces as "version unknown" in the status bar with no freshness indicator, prompting the user to investigate rather than falsely claiming up-to-date.

**Examples:**

- `2024.07.16` vs `2024.07.16` → `current`
- `2024.07.16` vs `2024.08.06` → `outdated`
- `2024.07.16.232931` (nightly) vs `2024.07.16` (PyPI stable) → `current` (installed >= latest by tuple compare)
- `2024.07.16` vs `` (empty/None) → `unknown`
- `master` vs `2024.07.16` → `unknown`

**Rationale:** yt-dlp's versioning is strictly date-based with an optional build-id suffix for stable releases. Tuple comparison after zero-padding handles all real-world cases. `packaging.version` is unnecessary and adds a dependency. The `unknown` outcome correctly handles the nightly-channel-on-stable-feed edge case from decision 3.

### 5. Threading and message-type isolation

**Decision:** A new `YtDlpUpdaterThread(threading.Thread)` in `powerhour/ytdlp_updater.py` mirrors `ProcessorThread`'s design. It accepts the existing `message_queue` and writes ONLY two namespaced message types plus the existing `log` type:

- `ytdlp_status` — single envelope with: `installed_version: Optional[str]`, `latest_version: Optional[str]`, `install_method: Literal[brew, pipx, pip, choco, standalone, unsupported, missing]`, `freshness: Literal[current, outdated, unknown, missing]`, `binary_path: Optional[str]`, `owning_python: Optional[str]`, `check_error: Optional[str]`, `unsupported_reason: Optional[str]`, `manual_command: Optional[str]`.
- `ytdlp_update_complete` — fired after an upgrade subprocess exits: `success: bool`, `exit_code: int`, `new_version: Optional[str]`, `latest_version: Optional[str]`, `reverified_freshness: Literal[current, outdated, unknown]`. `latest_version` carries the value used for the pre-upgrade freshness comparison so the GUI's stale-after-upgrade warning text does not depend on cached state.
- `log` — re-uses the existing log message type with `level` of `info`/`warning`/`error` for streaming subprocess output and diagnostic notes.

**The updater MUST NOT emit** `error`, `status`, `progress`, `video_progress`, or `complete`. The existing `error` handler at `powerhour_gui.py:1439-1451` is destructive (dialog + state reset + temp file cleanup), and `status` overwrites the user-visible status variable bound to the operation label. Cross-contamination would cause the updater to look like a failed processing job.

Two operation modes:

- `mode='check_only'`: query local + remote versions, classify install method, send one `ytdlp_status` message, exit.
- `mode='check_and_upgrade'`: do the check_only flow, then if `freshness == outdated` and the install method supports auto-upgrade, run the upgrade command with stdout+stderr merged via `subprocess.Popen(..., stderr=subprocess.STDOUT)`, line-iterated into `log` messages with appropriate level (lines starting with `WARNING:` → warning, `ERROR:` → error, else info). After exit, re-query installed version and send `ytdlp_update_complete`.

**Rationale:** This is the same threading pattern the GUI already uses. Namespacing the message types prevents collision with `ProcessorThread`'s message vocabulary. Zero new infrastructure beyond two `process_queue` handler branches.

**Alternatives considered:**

- *Two separate threads (one for check, one for upgrade).* Unnecessary; the upgrade flow always starts with a check anyway.
- *Synchronous network call wrapped in `after_idle`.* Cleaner-looking but harder to cancel and harder to stream subprocess output.

### 6. GUI placement: extend the existing status bar

**Decision:** Modify the existing `build_status_bar()` at `powerhour_gui.py:457` to add a new section between `operation_label` and `resource_label`. The existing `hint_label`, `operation_label`, `resource_label`, and `update_resource_usage()` 2-second poller are preserved unchanged.

New widgets inside `self.status_bar`:

- `self.ytdlp_version_label`: `ttk.Label` text `yt-dlp: <version>` or `yt-dlp: not installed` or `yt-dlp: version unknown`. Packed `side="right"` before `resource_label` in source order (which positions it to the LEFT of resource_label in Tk's pack geometry).
- `self.ytdlp_freshness_label`: `ttk.Label` text for the freshness indicator (` `, `• Up to date`, `• Update available: <ver>`, `• Required for URL downloads`). Color via foreground attribute: default for current, `#cc6600` (orange) for outdated, `#888888` (gray) for unknown/missing.
- `self.ytdlp_action_button`: `ttk.Button` with dynamic label (`Check for Update` / `Update yt-dlp` / `How to install`). Initial state `disabled`, enabled once the first `ytdlp_status` message arrives.
- A `ttk.Separator(orient='vertical')` between the yt-dlp section and `resource_label` for visual clarity.

The yt-dlp widgets do NOT use the existing `hint_label`/`operation_label`/`resource_label` — they are additive.

Three resulting status-bar states:

```
Up to date:
┌──────────────────────────────────────────────────────────────────┐
│ <hint>   <operation>   yt-dlp: 2026.03.17 • Up to date  │  <rsc> │
│                                          [Check for Update]      │
└──────────────────────────────────────────────────────────────────┘

Outdated:
┌──────────────────────────────────────────────────────────────────┐
│ <hint>   <operation>   yt-dlp: 2025.10.01 • Update available:    │
│                          2026.03.17       │  <rsc>               │
│                                          [Update yt-dlp]         │
└──────────────────────────────────────────────────────────────────┘

Missing:
┌──────────────────────────────────────────────────────────────────┐
│ <hint>   <operation>   yt-dlp: not installed • Required for URL  │
│                          downloads        │  <rsc>               │
│                                          [How to install]        │
└──────────────────────────────────────────────────────────────────┘
```

**Rationale:** Reusing the existing status bar is the only correct option — a second status bar at `row=4` would either collide or push the layout. The existing resource-monitoring is unrelated to yt-dlp and must be preserved.

### 7. Frozen-`.app` PATH handling on macOS

**Decision:** When `shutil.which('yt-dlp')` returns `None` AND `sys.platform == 'darwin'` AND `getattr(sys, 'frozen', False)` is true, retry the lookup using the user's actual login shell:

1. Determine the user's login shell from `os.environ.get('SHELL')` (set by Terminal.app and most login managers) with a fallback to `pwd.getpwuid(os.getuid()).pw_shell`.
2. Invoke that shell as a non-interactive login shell to discover the executable path:
   ```python
   subprocess.run(
       [user_shell, '-l', '-c', 'command -v yt-dlp'],
       capture_output=True, text=True, timeout=3
   )
   ```
3. If the shell is not in a small allowlist (`/bin/zsh`, `/bin/bash`, `/usr/local/bin/fish`, `/opt/homebrew/bin/fish`, `/bin/sh`), fall back to `/bin/sh -l -c '...'` which is POSIX-portable.
4. The shell is used ONLY for discovery. The resulting `yt-dlp` path is then invoked directly (no shell wrapper) for version queries and upgrade commands. Same for `brew` / `pipx` / package-manager binaries — we discover their absolute paths in the same login-shell pass and call them directly.

For upgrade subprocesses on a frozen `.app`, the upgrade argv list uses absolute paths discovered in this same way (e.g., `['/opt/homebrew/bin/brew', 'upgrade', 'yt-dlp']`). No shell wrapper is used at upgrade time, eliminating the side-effect concern of sourcing `.zshrc` on every upgrade run.

**Rationale:** macOS apps launched from Finder don't inherit shell environment. The original draft hardcoded `/bin/zsh`, which silently fails for users whose login shell is bash, fish, or sh. Using the user's actual shell respects their environment; using it only for discovery (not as a wrapper for the upgrade command itself) avoids running `.zshrc` side effects on every operation. The allowlist guards against an attacker-controlled `$SHELL`; the absolute-path invocation guards against PATH-injection in subsequent calls.

**Alternatives considered:**

- *Hard-code common paths* (`/opt/homebrew/bin`, `/usr/local/bin`, `~/.local/bin`). Brittle; misses pipx, nix, asdf, etc.
- *Read `/etc/paths` and `/etc/paths.d/*`.* Only captures system-level paths, misses user-level brew/pipx setups.
- *Prepend known paths to `os.environ['PATH']` at startup.* Same brittleness as the hard-coded option, plus it leaks into all subsequent subprocess calls.

### 8. Post-upgrade re-verification

**Decision:** After the upgrade subprocess exits with code 0, the updater re-runs the same binary discovery and version-query path it used at launch, and compares the new installed version against the same `latest_version` it queried before the upgrade ran. The `ytdlp_update_complete` message carries the re-queried `new_version` and the comparison result as `reverified_freshness`.

Outcomes:

- `reverified_freshness == 'current'`: status bar shows "Up to date" with the new version.
- `reverified_freshness == 'outdated'`: status bar keeps "Update available" (with the still-newer-than-installed latest), and the Output Log gets a warning-level line: `Package manager reported success but installed version (X) is still older than latest (Y) — the package manager's repo may lag the upstream release.`
- `reverified_freshness == 'unknown'`: status bar shows version unknown, info-level log line about the comparison failure.

**Rationale:** Package managers can exit 0 while updating to a version older than the upstream latest. brew formulas, conda channels, and choco packages all sometimes lag PyPI by hours or days. Without re-verification, the GUI would falsely claim "Up to date" immediately after a successful-but-stale upgrade.

### 9. Disable button during video processing

**Decision:** The GUI already tracks `self.processing_thread` and runs `reset_ui_state()` when processing ends. Add `self.ytdlp_action_button` to the set of widgets disabled/enabled by those state transitions, alongside the existing Start/Cancel/input controls.

**Rationale:** Running `brew upgrade` mid-processing could destabilize an in-flight download. Easier to disable than to coordinate two long-running operations.

## Risks / Trade-offs

- **Risk:** Install-method detection misclassifies a non-standard install (e.g., user moved a brew binary, installed via nix, conda env). → **Mitigation:** Path-pattern step 5 catches the common non-standard cases as `unsupported` and shows manual instructions. True edge cases that escape both step 5 and the pip-verification gate become `standalone` only if the binary lives in a user-writable directory, and `yt-dlp -U`'s own error message (`This is not a self-updateable build`) provides a clean fallback into the log panel.

- **Risk:** PyPI is unreachable for the user (corporate proxy, offline, certificate pinning issue). → **Mitigation:** All network errors degrade to "no freshness indicator" with a single info-level log line. The user can still manually click the button to retry.

- **Risk:** The frozen-`.app` login-shell discovery sources `.zshrc` / `.zprofile`, which can be slow or have arbitrary side effects. → **Mitigation:** Discovery runs with a 3-second timeout and is invoked only when `shutil.which` already failed (rare path). Upgrade subprocesses use the absolute path discovered, not a shell wrapper, so per-upgrade side effects are bounded to the one-time discovery call.

- **Risk:** Re-verification after a successful exit could fail (e.g., PyPI temporarily down) and mark a successful upgrade as `unknown`. → **Acceptance:** Better than falsely claiming "up to date". The user sees the upgrade succeeded (subprocess output in the log) and the verification was inconclusive.

- **Risk:** The pip-owning-Python verification (`yt_dlp.__file__` match) requires running the candidate interpreter to import yt_dlp. If the interpreter is broken or has C-extension load failures, verification fails and we reclassify to `unsupported`. → **Acceptance:** Correct conservative behavior; a broken Python install is not something we should silently upgrade.

- **Trade-off:** Streaming `brew upgrade` output into a `ScrolledText` panel will show brew's color-coded ANSI escapes as literal characters. → **Acceptance:** Acceptable. We can strip ANSI in a follow-up; for v1, raw is honest.

- **Trade-off:** Polling at 100ms (existing pattern) means slight latency between subprocess output and panel update. → **Acceptance:** Imperceptible to users.

## Migration Plan

No data migration. Code-only change. No config schema changes. No backward-compat concerns: launching an older build of the GUI will simply not show the yt-dlp status-bar section.

## Open Questions

- **Q1:** When the user has yt-dlp installed via both brew and pip (rare but happens), `shutil.which` returns the first on PATH. Do we just upgrade that one and ignore the other, or surface a warning that there are multiple? **Working answer:** Just upgrade the one on PATH; the install-method-detection log line names the resolved path so the user can see which.

- **Q2:** Should the launch-time check fire even when the user has no URL input (i.e., they're only using local folders)? **Working answer:** Yes — the status bar section is always visible and the cost is one HTTPS call. If we later add a setting to disable URL features entirely, the check can be gated on that.

- **Q3:** What if `yt-dlp --version` itself fails (corrupt install)? **Working answer:** `installed_version` becomes `None`, freshness becomes `unknown`, status bar shows "yt-dlp: error reading version", action button label remains `Check for Update` (clicking re-attempts the discovery, which may have been transient).

- **Q4:** Should the `unsupported` outcome display a per-method manual command (e.g., for conda: `conda update -c conda-forge yt-dlp`) or a generic "consult your package manager"? **Working answer:** Per-method when we recognize the method (conda, apt, dnf, pacman, nix, snap, flatpak, scoop, winget, npm, pyenv, asdf, mise); generic when we don't. The recognized commands are stored in a small dict in `ytdlp_updater.py`.
