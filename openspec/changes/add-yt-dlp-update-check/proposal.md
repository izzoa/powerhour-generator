## Why

yt-dlp is the project's most version-sensitive dependency: YouTube changes extractors frequently, and an outdated yt-dlp is the single most common real-world cause of "Failed to download playlist" errors in the GUI. The project does not pin yt-dlp (floor `>=2023.1.1` is a no-op in 2026), does not bundle it with the PyInstaller build, and provides no surface for users to see their installed version or refresh it without leaving the app. Users are stuck running whichever version they happened to install months or years ago, with no in-app affordance to discover or fix that.

## What Changes

- Extend the existing status bar at the bottom of the main GUI window (already defined at `powerhour/powerhour_gui.py:457`, currently holding `hint_label` / `operation_label` / `resource_label`) with a new section: the installed yt-dlp version, a freshness indicator, and a **Check for Update** button. The existing resource-usage poller and hint/operation labels are preserved unchanged.
- On app launch, query the PyPI JSON API in a background thread for the latest stable yt-dlp version and compare against the local version. If outdated, mark the new status-bar section visually (color change).
- On button click, run the upgrade command appropriate to how yt-dlp was installed: `brew upgrade yt-dlp`, `pipx upgrade yt-dlp`, `<owning-python> -m pip install -U yt-dlp`, `choco upgrade yt-dlp -y`, or `yt-dlp -U` for a true standalone binary. Stream the upgrade command's combined stdout+stderr into the existing Output Log panel.
- Detect the install method by inspecting the resolved binary path AND, for ambiguous cases, doing cheap secondary checks against the candidate package manager only. Classify into one of `brew`, `pipx`, `pip`, `choco`, `standalone`, `unsupported`, `missing`. The `unsupported` outcome (distro packages, conda, pyenv/asdf/mise shims, nix, snap, flatpak, scoop, winget, npm, etc.) shows the user a copy-paste manual upgrade command rather than guessing.
- Use new namespaced message types (`ytdlp_status`, `ytdlp_update_complete`) for cross-thread communication. The updater NEVER emits the generic `error` / `status` / `progress` / `complete` message types, which are owned by `ProcessorThread` and trigger processing-error dialogs and UI state resets.
- Handle the frozen-`.app` PATH problem on macOS by discovering the user's real PATH via their actual login shell (read from `$SHELL` / `pwd.getpwuid`), using the shell only for path discovery, then invoking the discovered absolute binaries directly.
- After an upgrade subprocess exits 0, re-query the installed version against the same latest source. Only show "Up to date" if the new version actually matches; otherwise log that the package manager did not provide the latest release.
- Disable the update button while a video-processing job is active, and gracefully no-op when yt-dlp is not installed at all (status section shows "not installed" and the button links to install docs).
- All network and subprocess work happens off the Tk main loop using the existing message-queue worker pattern; offline / DNS-failure / timeout cases degrade silently in the UI (no dialog, no status-bar freshness indicator) and log a single info-level line to the Output Log panel.

## Capabilities

### New Capabilities

- `yt-dlp-management`: Discover the installed yt-dlp version, detect how it was installed, compare against the upstream latest stable release on PyPI, and run the appropriate per-install-method upgrade command on user request. Includes the GUI status-bar surface that exposes this functionality.

### Modified Capabilities

<!-- None. No existing OpenSpec capabilities are defined for this codebase yet; the GUI status-bar additions are part of the new yt-dlp-management capability's surface, not a modification to a separately-specified gui capability. -->

## Impact

- **Code (modified):** `powerhour/powerhour_gui.py` — extend `build_status_bar()` to add yt-dlp version/freshness/button widgets without disturbing existing `hint_label` / `operation_label` / `resource_label` or `update_resource_usage()`. Extend `process_queue()` with two new message-type handlers. Wire the launch-time check after `process_queue` is scheduled.
- **Code (new):** `powerhour/ytdlp_updater.py` — new module containing the version-query (PyPI), install-method-detection, upgrade-runner logic, and worker thread that communicates with the GUI via the existing message queue using exclusively namespaced message types.
- **Tests (new):** Unit tests for the install-method detector (path-classification cases including symlinks, conda envs, pyenv shims, distro packages, frozen builds, all unsupported variants), the version comparator (date-style versions with and without build suffix, leading `v`, garbage input → `unknown`), and the post-upgrade re-verification logic.
- **Dependencies:** None added. Uses stdlib `urllib.request` for the PyPI JSON call, `subprocess` for upgrade execution, `shutil`/`os`/`pwd` (Unix) for path and shell inspection.
- **Network:** Adds one outbound HTTPS request to `pypi.org` on app launch (5s timeout). No telemetry, no other endpoints.
- **Out of scope (sibling problems left for separate changes):** The broader yt-dlp failure-reflection work identified during exploration (forwarding stderr into the log panel, removing the `[download]`-only stdout filter in `_download_playlist`, `--newline` flag, zero-files-after-exit-0 detection); pinning yt-dlp in `setup.py` / `requirements*.txt`; bundling yt-dlp into the PyInstaller build; supporting the yt-dlp nightly channel as a freshness source (`yt-dlp/yt-dlp-nightly-builds` repository) — nightly users whose version-tuple is newer than PyPI stable will see "Up to date" because the comparator returns `current` for installed-newer-than-latest, and the system will not prompt them to downgrade; auto-installing yt-dlp when missing.
