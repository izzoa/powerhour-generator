## 1. Updater module scaffolding

- [x] 1.1 Confirm `__version__` exists in `powerhour/__init__.py` (currently set to `"1.0.0"` at line 7) and is importable. All subsequent USER_AGENT references depend on this import. No code change required unless the constant has drifted from `setup.py`'s `VERSION`.
- [x] 1.2 Create `powerhour/ytdlp_updater.py` with module docstring and stdlib-only imports (`os`, `sys`, `shutil`, `subprocess`, `threading`, `queue`, `json`, `re`, `urllib.request`, `urllib.error`, `pwd` on Unix). Import `__version__` from `powerhour`.
- [x] 1.3 Define an `InstallMethod` type as `Literal['pipx', 'brew', 'choco', 'unsupported', 'pip', 'standalone', 'missing']`.
- [x] 1.4 Define a `Freshness` type as `Literal['current', 'outdated', 'unknown', 'missing']`.
- [x] 1.5 Define a `YtDlpStatus` dataclass with fields: `installed_version: Optional[str]`, `latest_version: Optional[str]`, `install_method: InstallMethod`, `freshness: Freshness`, `binary_path: Optional[str]`, `owning_python: Optional[str]`, `check_error: Optional[str]` (formatted as `"installed: <reason>"` or `"latest: <reason>"` or `"installed: <a>; latest: <b>"` when both fail), `unsupported_reason: Optional[str]`, `manual_command: Optional[str]`.
- [x] 1.6 Define module constants: `PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"`, `PYPI_TIMEOUT = 5.0`, `DISCOVERY_TIMEOUT = 3.0`, `INSTALLED_VERSION_TIMEOUT = 3.0`, `USER_AGENT = f"PowerHour-Generator/{__version__}"`, plus the manual-command dict mapping recognized `unsupported_reason` tags to per-method copy-paste commands.
- [x] 1.7 Define a `_normalize_path(p: str) -> str` helper that returns `p.replace('\\', '/')` and applies `casefold()` on Windows. All classifier pattern tests SHALL run against the normalized form.

## 2. Binary discovery and login-shell fallback

- [x] 2.1 Implement `find_ytdlp_binary() -> Optional[str]` that resolves `shutil.which('yt-dlp')` and applies `os.path.realpath` to dereference symlinks before returning.
- [x] 2.2 Implement `_login_shell_discover(target: str) -> Optional[str]` that determines the user's login shell from `os.environ.get('SHELL')` with fallback to `pwd.getpwuid(os.getuid()).pw_shell`, validates the shell against the allowlist `{/bin/zsh, /bin/bash, /usr/local/bin/fish, /opt/homebrew/bin/fish, /bin/sh}` with `/bin/sh` as final fallback for unrecognized shells, then invokes `<shell> -l -c 'command -v <target>'` with `DISCOVERY_TIMEOUT` and returns the stripped stdout or `None`.
- [x] 2.3 In `find_ytdlp_binary`, when `shutil.which` returns `None` AND `sys.platform == 'darwin'` AND `getattr(sys, 'frozen', False)` is true, call `_login_shell_discover('yt-dlp')` and use that result instead.
- [x] 2.4 Implement `find_package_manager_binary(name: str) -> Optional[str]` that does the same `shutil.which` + frozen-`.app` login-shell fallback for `brew`, `pipx`, and `choco`.
- [x] 2.5 Unit-test `find_ytdlp_binary` and `_login_shell_discover` with mocked `shutil.which`, `os.environ`, `pwd.getpwuid`, and `subprocess.run` covering: present on PATH, missing on PATH but found via zsh fallback, bash fallback, fish fallback, unrecognized shell falls back to sh, login-shell returns empty (still missing).

## 3. Install-method classification (path-pattern, ordered, normalized)

- [x] 3.1 Implement `classify_install_method(binary_path: str) -> tuple[InstallMethod, Optional[str], Optional[str]]` returning `(method, owning_python_hint, unsupported_reason)`. The function SHALL NOT return `missing` — the caller is responsible for handling the `binary_path is None` case before calling. The function's `InstallMethod` return is constrained to `{pipx, brew, choco, unsupported, pip, standalone}`.
- [x] 3.2 Apply `_normalize_path` to the input before any test. Execute pattern tests in this exact order: (1) pipx → (2) brew → (3) choco → (4) path-pattern unsupported (distro/shims/sandboxes/scoop/winget/npm) → (5) filesystem-augmented unsupported (conda env detected by sibling `conda-meta/` directory) → (6) pip (path contains `/site-packages/` OR shebang-based ownership verification) → (7) standalone (real executable in a user-writable directory).
- [x] 3.3 For step 6 (pip), extract the owning Python hint from either the `/site-packages/` parent's `bin/python*` sibling OR the binary's shebang line. On Windows, walk up two directories from `yt-dlp.exe` to find a sibling `python.exe`. Pass this hint to `verify_owning_python` (task §4); if verification fails, reclassify to `unsupported` with the verification failure reason.
- [x] 3.4 For step 4 (path-pattern unsupported), populate `unsupported_reason` with a short tag identifying the detected manager (`apt-or-dnf`, `pyenv-shim`, `asdf-shim`, `mise-shim`, `nix`, `snap`, `flatpak`, `scoop`, `winget`, `npm`). For step 5 (conda), use the tag `conda`.
- [x] 3.5 Unit-test the classifier with realistic path examples for each method AND for the critical ordering edge cases: a conda env binary whose shebang would verify as pip — must classify as `unsupported` with reason `conda`, not `pip`; a Debian `/usr/bin/yt-dlp` whose shebang points at `/usr/bin/python3` — must classify as `unsupported` with reason `apt-or-dnf`, not `pip`. Also cover: brew Apple Silicon, brew Intel, pipx, pip in a real venv (must classify `pip`), pip in conda env (must classify `conda`), pyenv shim, asdf shim, mise shim, nix store path, snap, flatpak, scoop, winget, npm global, standalone in `~/bin`, Windows chocolatey path with backslashes.

## 4. Pip-owning-Python verification

- [x] 4.1 Implement `verify_owning_python(binary_path: str, owning_python_hint: str) -> tuple[Optional[str], Optional[str]]` returning `(verified_python, unsupported_reason)`. `verified_python` is non-None only when ALL structural checks pass.
- [x] 4.2 Resolve the hint: handle `/usr/bin/env python3` shebangs via PATH lookup, dereference symlinks, return `None` if the resolved path does not exist.
- [x] 4.3 Detect shim interpreters by reading the file's first 256 bytes — pyenv/asdf/mise shims are shell scripts, real interpreters are ELF/Mach-O/PE binaries.
- [x] 4.4 Run `<python> -c "import yt_dlp; import sys; print(yt_dlp.__file__); print(sys.executable); print(sys.prefix); print(sys.base_prefix)"` with a 5s timeout. Parse the four lines.
- [x] 4.5 Compare the printed `yt_dlp.__file__` directory's `site-packages` root to the resolved `binary_path`'s `site-packages` root (walk up from the script until a `site-packages` directory is found). Refuse if they differ.
- [x] 4.6 Detect system-managed Python: if `sys.prefix == sys.base_prefix` (not in a venv), check for an `EXTERNALLY-MANAGED` marker at `<sys.prefix>/lib/python*/EXTERNALLY-MANAGED` and whether the interpreter's containing directory is writable. Refuse if either condition flags system-managed.
- [x] 4.7 Return `(None, '<reason-tag>')` on any failure with reason in {`shim-interpreter`, `system-managed-python`, `cannot-verify-owning-python`}, and `(verified_python, None)` on full success.
- [x] 4.8 Unit-test each refusal path independently with mocked subprocess output and filesystem state.

## 5. Version queries

- [x] 5.1 Implement `query_installed_version(binary_path: str) -> tuple[Optional[str], Optional[str]]` that runs `<binary_path> --version` with `INSTALLED_VERSION_TIMEOUT`, returning `(version, None)` on success and `(None, '<reason>')` on failure. Reason values: `timeout`, `exit_<N>`, `parse_error`, `oserror:<errno>`. This matches `query_latest_version`'s shape so both failure modes can be uniformly logged.
- [x] 5.2 Implement `query_latest_version(timeout: float = PYPI_TIMEOUT) -> tuple[Optional[str], Optional[str]]` returning `(latest_version, error_description)`. GETs `PYPI_URL` with `User-Agent: {USER_AGENT}`, parses JSON, returns `(info.version, None)` on success or `(None, '<reason>')` on any timeout / HTTP error / JSON parse error.
- [x] 5.3 Implement `compare_versions(installed: Optional[str], latest: Optional[str]) -> Freshness`. Parse both as integer tuples after stripping any leading `v`, padding the shorter to match length, and treating any parse failure or `None` as `unknown`. Return `current` when `installed >= latest`, `outdated` when `installed < latest`.
- [x] 5.4 Unit-test the comparator with: equal versions, installed older by patch, installed older by year, installed has build suffix vs. latest doesn't, latest has build suffix vs. installed doesn't, leading `v` on either side, `None` on either side, `master` / garbage string on either side (→ `unknown`).
- [x] 5.5 Implement `format_check_error(installed_err: Optional[str], latest_err: Optional[str]) -> Optional[str]` returning `None` when both are `None`, `"installed: <reason>"` when only installed failed, `"latest: <reason>"` when only latest failed, or `"installed: <a>; latest: <b>"` when both failed. Used to populate `YtDlpStatus.check_error`.

## 6. Upgrade command resolution

- [x] 6.1 Implement `build_upgrade_command(status: YtDlpStatus) -> Optional[list[str]]` returning the argv list for an auto-upgrade per verified install method, or `None` for `unsupported` / `missing` / unverified `pip`.
- [x] 6.2 For each supported method, use absolute paths discovered via `find_package_manager_binary` rather than relying on PATH inside the subprocess:
   - `brew` → `[<brew_abs>, 'upgrade', 'yt-dlp']`
   - `pipx` → `[<pipx_abs>, 'upgrade', 'yt-dlp']`
   - `choco` → `[<choco_abs>, 'upgrade', 'yt-dlp', '-y']`
   - `pip` (verified) → `[<verified_python>, '-m', 'pip', 'install', '-U', 'yt-dlp']`
   - `standalone` → `[<binary_path>, '-U']`
- [x] 6.3 Implement `build_manual_upgrade_instructions(status: YtDlpStatus) -> str` returning the per-method copy-paste command string. Use the manual-command dict from task 1.6 keyed on `unsupported_reason`, falling back to a generic "consult your package manager" message when the reason tag is unrecognized.
- [x] 6.4 Unit-test `build_upgrade_command` for each verified method (each must produce an argv list with absolute first element) and `build_manual_upgrade_instructions` for each known unsupported reason plus the generic fallback.

## 7. Worker thread

- [x] 7.1 Implement `class YtDlpUpdaterThread(threading.Thread)` with `__init__(message_queue: queue.Queue, mode: Literal['check_only', 'check_and_upgrade'])`, `daemon=True`.
- [x] 7.2 In `run()`, execute the discovery flow: call `find_ytdlp_binary`. If `None`, build a `YtDlpStatus` with `install_method='missing'`, `freshness='missing'`, and enqueue one `ytdlp_status` message; return. Otherwise call `classify_install_method` → `verify_owning_python` (when pip) → `query_installed_version` → `query_latest_version` → `compare_versions` → `format_check_error`, assemble a `YtDlpStatus`, enqueue one `ytdlp_status` message.
- [x] 7.3 In `check_and_upgrade` mode, after the initial status message, branch on `freshness`. **The mode MUST emit a `ytdlp_update_complete` message on every path before returning**, so the GUI always clears `_ytdlp_update_in_progress` and re-enables the action button.
- [x] 7.4 `freshness == 'outdated'` AND `build_upgrade_command(status)` returns a non-None argv: run that argv via `subprocess.Popen(..., stderr=subprocess.STDOUT)`, iterating lines from the merged stream and enqueueing `log` messages with level chosen by line prefix (`WARNING:` → warning, `ERROR:` → error, else info). After exit, re-run `find_ytdlp_binary` + `query_installed_version`, compute `reverified_freshness` via `compare_versions` against the cached `latest_version`, and enqueue `{'type': 'ytdlp_update_complete', 'success': exit_code == 0, 'exit_code': N, 'new_version': new_version, 'latest_version': cached_latest, 'reverified_freshness': reverified_freshness}`. The `latest_version` field is included so the GUI's stale-after-upgrade warning text does not depend on cached `_ytdlp_status`.
- [x] 7.5 `freshness == 'outdated'` but `build_upgrade_command` returns `None` (unsupported / unverified): enqueue an info-level `log` message with the manual command from `build_manual_upgrade_instructions`, then enqueue `ytdlp_update_complete` with `success=False, exit_code=-2` (sentinel for "no auto-upgrade available"), `new_version=installed_version`, `latest_version=cached_latest`, `reverified_freshness=freshness`. This re-enables the action button.
- [x] 7.6 `freshness == 'current'`: the fresh check confirms the install is already up to date. Enqueue an info-level `log` message `yt-dlp is already up to date (latest: <latest_version>)`, then enqueue `ytdlp_update_complete` with `success=True, exit_code=0, new_version=installed_version, latest_version=latest_version, reverified_freshness='current'`. No subprocess runs.
- [x] 7.7 `freshness == 'unknown'` (version comparison failed) OR `install_method == 'missing'` (yt-dlp disappeared between the launch check and the click): enqueue an info-level `log` message describing the state, then enqueue `ytdlp_update_complete` with `success=False, exit_code=-3` (sentinel for "cannot determine freshness or binary"), `new_version=installed_version`, `latest_version=latest_version`, `reverified_freshness=freshness`. This re-enables the action button without falsely claiming success.
- [x] 7.8 Wrap the entire `run()` body in `try/except`. On any unhandled exception, enqueue a single `log` message at error level AND a `ytdlp_update_complete` with `success=False, exit_code=-1` (in upgrade mode) or a `ytdlp_status` with `check_error` populated and `freshness='unknown'` (in check-only mode). NEVER enqueue a generic `error` / `status` / `progress` / `video_progress` / `complete` message.
- [x] 7.9 Add a unit test that calls `check_and_upgrade` with a mocked `freshness='current'` state and asserts: exactly one `ytdlp_status` message, one info-level `log` message containing "already up to date", and one `ytdlp_update_complete` with `success=True, reverified_freshness='current'`. Mirror the test for `freshness='unknown'` asserting `success=False, exit_code=-3`.

## 8. GUI: extend the existing status bar

- [x] 8.1 Modify `PowerHourGUI.build_status_bar()` in `powerhour/powerhour_gui.py` (around line 457). Do NOT add a new method; do NOT change the grid position or remove existing widgets.
- [x] 8.2 After the existing `self.resource_label.pack(side="right", padx=5)` line, add a `ttk.Separator(self.status_bar, orient='vertical')` packed `side="right", fill="y", padx=5`. (Tk packs right-anchored items right-to-left in source order, so this separator ends up to the LEFT of `resource_label`.)
- [x] 8.3 Add `self.ytdlp_action_button = ttk.Button(self.status_bar, text="Check for Update", state="disabled", command=self.on_update_ytdlp_clicked)` packed `side="right", padx=5`.
- [x] 8.4 Add `self.ytdlp_freshness_label = ttk.Label(self.status_bar, text="", font=("Arial", 9))` packed `side="right", padx=2`.
- [x] 8.5 Add `self.ytdlp_version_label = ttk.Label(self.status_bar, text="yt-dlp: …", font=("Arial", 9))` packed `side="right", padx=2`.
- [x] 8.6 Leave `self.hint_label`, `self.operation_label`, `self.resource_label`, and the `self.update_resource_usage()` scheduling untouched. The 2-second poller continues writing to `resource_label`.

## 9. GUI: namespaced queue handlers

- [x] 9.1 In `PowerHourGUI.process_queue()` (around line 1389), add a handler branch for `message['type'] == 'ytdlp_status'` that:
   - Stores the message contents on `self._ytdlp_status` for the click handler to consult.
   - Updates `ytdlp_version_label` text based on `installed_version` and `install_method`.
   - Updates `ytdlp_freshness_label` text and foreground color based on `freshness` and `install_method` (default for current, `#cc6600` orange for outdated, `#888888` gray for unknown/missing).
   - Updates `ytdlp_action_button` label and state based on `install_method` and `freshness` (enables the button only if no processing is active and no updater is in progress).
- [x] 9.2 Add a handler branch for `message['type'] == 'ytdlp_update_complete'` that:
   - Clears `self._ytdlp_update_in_progress = False`.
   - If `success` and `reverified_freshness == 'current'`: refresh version label with `new_version`, set freshness to "Up to date", log info `yt-dlp updated to <new_version>`.
   - If `success` and `reverified_freshness == 'outdated'`: refresh version label with `new_version`, keep `• Update available: <latest_version>` indicator using the `latest_version` from the message envelope, log warning `Package manager reported success but installed version (<new_version>) is still older than latest (<latest_version>) — the package manager's repo may lag the upstream release`.
   - If `success` and `reverified_freshness == 'unknown'`: refresh version label to "version unknown", log info about the re-verification failure.
   - If `not success`: leave status bar in its prior state.
   - In all cases: re-enable the action button if `not self._processing_active` (button stays disabled while a processing job runs even after the updater finishes).
- [x] 9.3 Add these branches BEFORE the existing `error` branch so the new types are matched first and never fall through into the destructive processing-error path.
- [x] 9.4 Add a unit test that exercises `YtDlpUpdaterThread.run()` with all subprocess/network calls mocked and asserts that no message of type `error`, `status`, `progress`, `video_progress`, or `complete` is ever emitted (drain the queue, fail on any disallowed type).
- [x] 9.5 Initialize `self._ytdlp_status = None` and `self._ytdlp_update_in_progress = False` in `PowerHourGUI.__init__` before `build_status_bar` runs.

## 10. GUI: launch-time check wiring

- [x] 10.1 In `PowerHourGUI.__init__`, after `self.process_queue()` is first called (it both consumes any pending messages AND schedules its own next run via `self.after(100, ...)` at `powerhour_gui.py:1457`), instantiate `YtDlpUpdaterThread(self.message_queue, mode='check_only')` and call `start()`. The thread MUST start after the first `process_queue()` invocation so the queue has a registered consumer; queue buffering keeps this safe but the ordering pins the test.
- [x] 10.2 Add an assertion (or comment) at this call site documenting that the thread is launched off-main-loop and that no blocking call to PyPI or `yt-dlp --version` happens on the Tk thread before `mainloop()` enters.

## 11. GUI: manual update click handler

- [x] 11.1 Implement `PowerHourGUI.on_update_ytdlp_clicked(self) -> None` that branches on `self._ytdlp_status.install_method`:
   - `missing`: open `YTDLP_INSTALL_DOCS_URL` via `webbrowser.open(...)`.
   - All other methods: set `self._ytdlp_update_in_progress = True`, disable the action button, instantiate `YtDlpUpdaterThread(self.message_queue, mode='check_and_upgrade')`, and call `start()`.
- [x] 11.2 Guard against `self._ytdlp_status is None` (button click before first launch-time check returns) — log a warning and return without action.

## 12. GUI: disable during processing, race-safe re-enable

- [x] 12.1 In the existing code path that transitions widgets to the processing-active state (find where Start/Cancel/input controls are disabled), set `self._processing_active = True` and add `self.ytdlp_action_button.config(state='disabled')`.
- [x] 12.2 In `reset_ui_state()`, set `self._processing_active = False`. Re-enable `self.ytdlp_action_button` ONLY when `not self._ytdlp_update_in_progress`. If an updater run is still active, the `ytdlp_update_complete` handler at task 9.2 will re-enable the button when the updater finishes (also gated on `not self._processing_active`).
- [x] 12.3 Initialize `self._processing_active = False` in `PowerHourGUI.__init__` before `build_status_bar` runs.
- [x] 12.4 Add a unit test that simulates the race: start a fake processing job, start a fake updater run, end the processing job first (assert button stays disabled), then complete the updater (assert button becomes enabled).

## 13. Tests

- [x] 13.1 Add `tests/test_ytdlp_updater.py` covering all unit tests from tasks 2.5, 3.5, 4.8, 5.4, 6.4, 9.4, and 12.4. Use `unittest.mock.patch` for `shutil.which`, `os.path.realpath`, `subprocess.run`, `subprocess.Popen`, `urllib.request.urlopen`, and `pwd.getpwuid`.
- [x] 13.2 Add a queue-protocol test that spawns `YtDlpUpdaterThread` in `check_only` mode with all subprocess and network calls mocked, drains the queue, and asserts: exactly one `ytdlp_status` message arrives, no `error` / `status` / `progress` / `video_progress` / `complete` messages are ever enqueued.
- [x] 13.3 Add a queue-protocol test for `check_and_upgrade` that mocks an outdated state, a successful subprocess (exit 0 with newline-terminated output and one `WARNING:` line), a post-upgrade re-query that returns the new latest, and asserts: one `ytdlp_status`, then `log` messages with correct levels per prefix, then one `ytdlp_update_complete` with `success=True, reverified_freshness='current', latest_version=<expected>`.
- [x] 13.4 Add a test for the "exit 0 but still outdated" scenario: mock a subprocess that exits 0 but the post-upgrade `query_installed_version` returns the same older version. Assert `ytdlp_update_complete` has `success=True, reverified_freshness='outdated', latest_version=<expected>`, and that a warning-level log message containing both the new (still older) version and the latest version was enqueued.
- [x] 13.5 Add a GUI smoke test that constructs `PowerHourGUI` with a stubbed updater thread and verifies: (a) the new status-bar widgets (`ytdlp_version_label`, `ytdlp_freshness_label`, `ytdlp_action_button`) exist on the instance; (b) the pre-existing `hint_label` / `operation_label` / `resource_label` still exist and have not been removed; (c) `update_resource_usage` is still scheduled. **Skip the test cleanly when no display is available** (`pytest.skip` when `tkinter.Tk()` raises `tkinter.TclError`, or when `os.environ.get('DISPLAY')` is unset on Linux and `sys.platform != 'darwin'`); CI runners without a graphics layer should not fail on this test.
- [x] 13.6 Verify the full existing test suite still passes with no regressions.

## 14. Docs and constants

- [x] 14.1 Update `docs/README_GUI.md` to mention the new yt-dlp section of the status bar and the update action.
- [x] 14.2 Update `docs/USER_GUIDE.md` to add a "Keeping yt-dlp up to date" subsection covering the in-app button, the per-OS manual commands shown for unsupported install methods, and a note that nightly-channel users will see PyPI's stable as latest (and the comparator will mark their newer nightly as "Up to date").
- [x] 14.3 Add a one-line entry to `docs/CHANGELOG.md` under an Unreleased section: "Added yt-dlp version display and in-app update button to the existing GUI status bar."
- [x] 14.4 Define `YTDLP_INSTALL_DOCS_URL` at the top of `powerhour/ytdlp_updater.py` pointing to a stable destination. Document the choice: either the README's `#yt-dlp` anchor on the project's GitHub (e.g., `https://github.com/<owner>/powerhour-generator#yt-dlp`) or a docs page. Whichever is chosen, add the anchor/section to the target file in the same change so the link is not broken on landing.

## 15. Manual validation

- [x] 15.1 macOS dev install (terminal-launched): confirm status bar shows correct version on launch, shows outdated indicator if a newer release exists on PyPI, clicking the button runs the correct upgrade command and streams output to the Output Log, and post-upgrade re-verification updates the indicator correctly.
- [ ] 15.2 macOS frozen `.app` (Finder-launched): confirm the login-shell discovery finds brew-installed yt-dlp via the user's actual login shell (test with both zsh and bash), version displays correctly, and the upgrade subprocess is invoked using absolute paths (verify by inspecting subprocess argv).
- [ ] 15.3 With yt-dlp uninstalled: confirm status bar shows "not installed", action button labeled "How to install", clicking opens the docs URL, and no spurious error dialog fires. The classifier is NOT invoked in this case (discovery returns None and the worker emits `missing` directly).
- [ ] 15.4 With network offline (disable Wi-Fi or block PyPI): confirm the launch-time check fails silently in the UI, status bar shows only the installed version, a single info-level line appears in the Output Log with the PyPI failure reason, and no error dialog appears.
- [ ] 15.5 With a deliberately outdated yt-dlp installed via pip in a venv: confirm pip-owning Python verification succeeds and the upgrade runs via `<venv-python> -m pip install -U yt-dlp`.
- [ ] 15.6 With yt-dlp installed via apt on a Debian VM: confirm classification is `unsupported` with `unsupported_reason='apt-or-dnf'`, the Output Log shows the apt-specific manual command, no auto-upgrade runs, and no error dialog appears.
- [x] 15.7 With yt-dlp installed via conda: confirm classification is `unsupported` with `unsupported_reason='conda'` (the filesystem-augmented check fires because of a sibling `conda-meta/` directory), the Output Log shows the conda-forge manual command, NOT a pip command.
- [ ] 15.8 Race test: start a PowerHour processing job, click "Check for Update" before the job ends (the button should already be disabled, so this is a UI-only verification), then let the job finish. Confirm the update button is properly re-enabled and clicking it now starts an updater run.
- [x] 15.9 Confirm the existing status bar widgets (hint, operation, resource) still render and the resource poller still updates every 2 seconds after the changes.
