## ADDED Requirements

### Requirement: Display installed yt-dlp version in the existing status bar

The system SHALL extend the existing status bar (defined at `powerhour/powerhour_gui.py:457`) with a new section showing the installed yt-dlp version. The existing `hint_label`, `operation_label`, `resource_label`, and the `update_resource_usage()` 2-second poller SHALL be preserved unchanged.

#### Scenario: yt-dlp is installed and reports a version

- **WHEN** the GUI launches and `yt-dlp --version` returns a value parseable as a date-style version
- **THEN** the new status-bar section SHALL show `yt-dlp: <version>` in the default foreground color
- **AND** the existing `hint_label`, `operation_label`, and `resource_label` SHALL continue to display their pre-existing contents

#### Scenario: yt-dlp is not installed

- **WHEN** the GUI launches and binary discovery (including the platform-appropriate PATH fallback) returns `None`
- **THEN** the new status-bar section SHALL show `yt-dlp: not installed` in a neutral gray color
- **AND** the action button SHALL be labeled `How to install`
- **AND** clicking the action button SHALL open the installation documentation in the user's default browser

#### Scenario: yt-dlp is installed but `--version` fails

- **WHEN** the binary is discovered but invoking it with `--version` exits non-zero, raises an exception, or returns output that does not parse as a version
- **THEN** the new status-bar section SHALL show `yt-dlp: version unknown` in a neutral gray color
- **AND** an info-level entry SHALL be written to the Output Log panel describing the failure

### Requirement: Check for newer yt-dlp release on launch

The system SHALL perform an asynchronous check for the latest yt-dlp stable release at app launch, comparing the installed version against the PyPI JSON API. The check MUST NOT block the Tk main loop and MUST degrade silently in the UI on network failure while logging a single diagnostic line.

#### Scenario: Installed version is current

- **WHEN** the launch-time check completes successfully and the version comparator returns `current`
- **THEN** the status-bar section SHALL append `• Up to date` after the version label
- **AND** the action button SHALL be labeled `Check for Update`

#### Scenario: Installed version is outdated

- **WHEN** the launch-time check completes successfully and the version comparator returns `outdated`
- **THEN** the status-bar section SHALL append `• Update available: <latest_version>` in orange
- **AND** the action button SHALL be labeled `Update yt-dlp`

#### Scenario: Version comparison returns unknown

- **WHEN** the launch-time check returns versions that cannot be parsed as integer tuples on one or both sides
- **THEN** the status-bar section SHALL NOT show any freshness indicator
- **AND** an info-level entry SHALL be written to the Output Log describing which side failed to parse
- **AND** the system SHALL NOT claim the installed version is up to date

#### Scenario: Launch-time check fails due to network error

- **WHEN** the PyPI request times out, returns a non-2xx HTTP status, raises a connection error, or returns a response body that cannot be parsed as JSON
- **THEN** the status-bar section SHALL show only the installed version with no freshness indicator
- **AND** no dialog SHALL be raised
- **AND** exactly one info-level entry SHALL be written to the Output Log describing the failure mode (e.g., timeout, HTTP status, parse error)

### Requirement: Detect yt-dlp install method

The system SHALL classify the installed yt-dlp binary into exactly one of: `pipx`, `brew`, `choco`, `unsupported`, `pip`, `standalone`, or `missing`. Classification SHALL occur after binary discovery, against the realpath-resolved and (on Windows) separator-normalized path. The classifier SHALL run pattern tests in the order listed below; unsupported-manager checks MUST execute before `pip` detection so that conda envs and distro packages do not falsely match the `pip` shebang-verification path.

#### Scenario: yt-dlp is missing (handled at discovery layer)

- **WHEN** binary discovery (including the platform-appropriate PATH fallback) returns `None`
- **THEN** the install method SHALL be reported as `missing` directly by the discovery flow
- **AND** the classifier SHALL NOT be invoked

#### Scenario: pipx install

- **WHEN** the resolved, normalized path contains `/pipx/`
- **THEN** the install method SHALL be classified as `pipx`

#### Scenario: Homebrew install on macOS

- **WHEN** the resolved, normalized path contains `/Cellar/yt-dlp/` or starts with `/opt/homebrew/` or `/usr/local/Cellar/`
- **AND** the path does not match the pipx pattern above
- **THEN** the install method SHALL be classified as `brew`

#### Scenario: Chocolatey install on Windows

- **WHEN** the resolved, normalized path contains `/chocolatey/`
- **THEN** the install method SHALL be classified as `choco`

#### Scenario: Path-pattern unsupported manager

- **WHEN** the resolved, normalized path starts with `/nix/store/`, `/snap/`, `/var/lib/flatpak/`, `/usr/bin/`, or `/usr/sbin/`, OR matches `/.pyenv/shims/`, `/.asdf/shims/`, `/.local/share/mise/shims/`, `/scoop/`, `/microsoft/winget/`, or `/lib/node_modules/`
- **AND** the path does not match any prior scenario
- **THEN** the install method SHALL be classified as `unsupported`
- **AND** `unsupported_reason` SHALL be set to a tag identifying the detected manager (e.g., `apt-or-dnf`, `pyenv-shim`, `asdf-shim`, `mise-shim`, `nix`, `snap`, `flatpak`, `scoop`, `winget`, `npm`)

#### Scenario: Conda environment (filesystem-augmented unsupported)

- **WHEN** the binary's parent directory contains a sibling directory named `conda-meta/`
- **AND** the path does not match any prior scenario
- **THEN** the install method SHALL be classified as `unsupported`
- **AND** `unsupported_reason` SHALL be set to `conda`

#### Scenario: pip install in a Python site-packages

- **WHEN** the resolved path contains `/site-packages/` OR the binary's shebang resolves to a Python interpreter that owns the same `yt_dlp` module (per the pip-owning-Python verification requirement)
- **AND** the path does not match any prior scenario (pipx, brew, choco, path-pattern unsupported, or conda)
- **THEN** the install method SHALL be classified as `pip`
- **AND** the system SHALL record the owning Python interpreter path for verification

#### Scenario: Standalone binary (true user-controlled install)

- **WHEN** the resolved path is an executable file in a user-writable directory and does not match any pattern in the prior scenarios
- **THEN** the install method SHALL be classified as `standalone`

### Requirement: Verify pip-owning Python before auto-upgrading

When the install method is classified as `pip`, the system SHALL verify the owning Python interpreter structurally before running any upgrade command. If verification fails, the install method SHALL be reclassified as `unsupported` for the duration of the click handler.

#### Scenario: Owning Python verification succeeds

- **WHEN** the discovered interpreter exists, is executable, is not a pyenv/asdf/mise shim, runs `import yt_dlp; print(yt_dlp.__file__)` successfully, and the printed module path is rooted in the same `site-packages` directory tree as the resolved `yt-dlp` script
- **AND** the interpreter's `sys.prefix != sys.base_prefix` (in a venv) OR no `EXTERNALLY-MANAGED` marker exists alongside its stdlib
- **AND** the interpreter's containing directory is writable by the current user
- **THEN** the `pip` classification SHALL stand and `<owning_python> -m pip install -U yt-dlp` SHALL be used for the upgrade

#### Scenario: Owning Python is system-managed

- **WHEN** verification finds the interpreter is not in a venv AND an `EXTERNALLY-MANAGED` marker exists OR the interpreter's directory is not user-writable OR the interpreter lives in `/usr/bin`, `/usr/local/bin`, `/usr/sbin`, or a macOS Framework path
- **THEN** the install method SHALL be reclassified as `unsupported`
- **AND** `unsupported_reason` SHALL be set to `system-managed-python`

#### Scenario: Owning Python is a shim

- **WHEN** verification finds the discovered interpreter is a pyenv, asdf, or mise shim (file is a shell script dispatching to a real interpreter)
- **THEN** the install method SHALL be reclassified as `unsupported`
- **AND** `unsupported_reason` SHALL be set to `shim-interpreter`

#### Scenario: Owning Python cannot import yt_dlp or paths do not match

- **WHEN** running `import yt_dlp` exits non-zero, OR prints a path that is not within the same site-packages root as the resolved `yt-dlp` script
- **THEN** the install method SHALL be reclassified as `unsupported`
- **AND** `unsupported_reason` SHALL be set to `cannot-verify-owning-python`

### Requirement: Run install-method-appropriate upgrade command

The system SHALL execute an upgrade command that matches the verified install method. The system MUST NOT execute `yt-dlp -U` for any install method other than `standalone`.

#### Scenario: Upgrade a brew install

- **WHEN** the verified install method is `brew` and the user clicks the update action
- **THEN** the system SHALL run `<absolute_brew_path> upgrade yt-dlp` where the brew path is discovered via the same mechanism as the yt-dlp path

#### Scenario: Upgrade a pipx install

- **WHEN** the verified install method is `pipx` and the user clicks the update action
- **THEN** the system SHALL run `<absolute_pipx_path> upgrade yt-dlp`

#### Scenario: Upgrade a choco install

- **WHEN** the verified install method is `choco` and the user clicks the update action
- **THEN** the system SHALL run `<absolute_choco_path> upgrade yt-dlp -y`

#### Scenario: Upgrade a verified pip install

- **WHEN** the verified install method is `pip` and the owning Python passed verification
- **THEN** the system SHALL run `<verified_owning_python> -m pip install -U yt-dlp`

#### Scenario: Upgrade a standalone binary

- **WHEN** the verified install method is `standalone`
- **THEN** the system SHALL run `<resolved_yt_dlp_path> -U`

#### Scenario: Unsupported install method

- **WHEN** the install method is `unsupported` (either via path classification or pip-verification reclassification)
- **THEN** the system SHALL NOT auto-run any upgrade
- **AND** the Output Log SHALL receive an info-level entry containing a manual upgrade command appropriate to the detected manager (e.g., `conda update -c conda-forge yt-dlp`, `sudo apt update && sudo apt install --only-upgrade yt-dlp`, or a generic "consult your package manager" when the manager is unrecognized)
- **AND** the status-bar section SHALL keep its prior freshness state

### Requirement: Stream upgrade command output to the Output Log

The system SHALL pipe the upgrade subprocess's combined stdout and stderr into the existing GUI Output Log panel, using the existing `log` message type. Output SHALL be parsed line-by-line on newline boundaries; carriage-return-overwritten progress lines may appear as a single long line until a newline terminates them.

#### Scenario: Successful upgrade with newline-terminated output

- **WHEN** the upgrade subprocess exits with code 0
- **THEN** every newline-terminated line of the combined output SHALL appear in the Output Log panel at info level
- **AND** lines starting with `WARNING:` SHALL be rendered at warning level
- **AND** lines starting with `ERROR:` SHALL be rendered at error level
- **AND** the system SHALL re-query the installed version and compare against the same latest version used for the pre-upgrade check (see *Verify update result after exit code 0*)

#### Scenario: Failed upgrade

- **WHEN** the upgrade subprocess exits with a non-zero code
- **THEN** every newline-terminated line of the combined output SHALL appear in the Output Log panel
- **AND** a final `log` entry SHALL be sent at error level with text `yt-dlp update failed (exit code <N>)`
- **AND** the status-bar section SHALL retain its prior state

#### Scenario: Upgrade subprocess cannot be started

- **WHEN** the upgrade subprocess raises an exception before any output is produced (e.g., the upgrade tool is not on PATH)
- **THEN** the exception message SHALL be written to the Output Log at error level
- **AND** the status-bar section SHALL retain its prior state

### Requirement: Verify update result after exit code 0

The system SHALL re-query the installed yt-dlp version after a successful upgrade subprocess (exit code 0) and compare against the same latest version it used for the pre-upgrade freshness check. Status-bar updates SHALL be based on this re-verification, not on the subprocess exit code alone.

#### Scenario: Upgrade successfully advanced the installed version to current

- **WHEN** post-upgrade re-verification returns `current`
- **THEN** the status-bar section SHALL show the new version with `• Up to date`
- **AND** an info-level entry SHALL be written to the Output Log: `yt-dlp updated to <new_version>`

#### Scenario: Upgrade exited 0 but the installed version is still outdated

- **WHEN** post-upgrade re-verification returns `outdated`
- **THEN** the status-bar section SHALL retain the `• Update available: <latest>` indicator with the new (still-outdated) installed version
- **AND** a warning-level entry SHALL be written to the Output Log: `Package manager reported success but installed version (<new_version>) is still older than latest (<latest_version>) — the package manager's repo may lag the upstream release`

#### Scenario: Re-verification itself fails

- **WHEN** post-upgrade re-verification cannot complete (e.g., binary discovery now returns `None`, version parse fails)
- **THEN** the status-bar section SHALL show `yt-dlp: version unknown`
- **AND** an info-level entry SHALL be written to the Output Log describing the re-verification failure

### Requirement: Updater uses namespaced messages only

The yt-dlp updater worker thread SHALL emit only the following message types to the shared `message_queue`: `ytdlp_status`, `ytdlp_update_complete`, and `log`. It MUST NOT emit `error`, `status`, `progress`, `video_progress`, or `complete`. The GUI's `process_queue` handler SHALL recognize the new types and route them to the status-bar section without invoking the existing processing-error or processing-complete code paths.

#### Scenario: Updater encounters a fatal error during launch-time check

- **WHEN** the launch-time check raises an unhandled exception
- **THEN** the updater SHALL emit a `log` message at error level describing the failure
- **AND** the updater SHALL emit a `ytdlp_status` message with `check_error` populated and `freshness` set to `unknown`
- **AND** no `error` message SHALL be enqueued
- **AND** the existing "Processing Error" dialog and `reset_ui_state()` paths SHALL NOT be invoked

#### Scenario: Updater encounters a fatal error during an upgrade

- **WHEN** the upgrade-mode run raises an unhandled exception
- **THEN** the updater SHALL emit a `log` message at error level
- **AND** the updater SHALL emit a `ytdlp_update_complete` message with `success=False` and `exit_code=-1`
- **AND** no `error` message SHALL be enqueued

### Requirement: Disable update action during video processing

The system SHALL disable the update action button while a `ProcessorThread` is active, and re-enable it when processing completes, errors out, or is cancelled.

#### Scenario: Processing starts

- **WHEN** the user starts a PowerHour processing job and the GUI transitions to the processing-active UI state
- **THEN** the update action button SHALL become disabled (visibly greyed and non-clickable)

#### Scenario: Processing finishes

- **WHEN** `reset_ui_state()` runs (after successful completion, processing error, or user cancellation)
- **THEN** the update action button SHALL be re-enabled

### Requirement: All network and subprocess work runs off the Tk main loop

The system SHALL execute all yt-dlp version queries, PyPI requests, and upgrade subprocesses on a background `threading.Thread`. The Tk main loop MUST NOT make any blocking network or subprocess call before `mainloop()` enters its first iteration.

#### Scenario: Launch-time check is in flight

- **WHEN** the GUI has constructed its widgets, scheduled `process_queue` via `self.after(100, ...)`, and entered `mainloop()`
- **THEN** the launch-time check SHALL be running on a `YtDlpUpdaterThread`, not on the main thread
- **AND** the new status-bar section SHALL initially show only the version label (or `yt-dlp: …` if the binary query has not yet returned)
- **AND** the action button SHALL be disabled until the first `ytdlp_status` message arrives

#### Scenario: Upgrade is running

- **WHEN** an upgrade subprocess is executing on the worker thread
- **THEN** the main window SHALL remain interactive (inputs, menus, log scrolling all respond)
- **AND** the Output Log panel SHALL receive new lines as they are produced (subject to newline-terminated buffering)

### Requirement: Handle the frozen-`.app` PATH inheritance gap on macOS

When the application is running as a frozen PyInstaller bundle on macOS launched from Finder, the process inherits a minimal PATH that excludes Homebrew, pipx, and user-local install locations. The system SHALL compensate by invoking the user's actual login shell to discover binary paths, then call the discovered binaries directly without further shell wrapping.

#### Scenario: Frozen .app with brew-installed yt-dlp, user shell is zsh

- **WHEN** `sys.platform == 'darwin'`, `getattr(sys, 'frozen', False)` is true, `shutil.which('yt-dlp')` returns `None`, and `os.environ.get('SHELL')` is `/bin/zsh` (or `pwd.getpwuid(os.getuid()).pw_shell` returns the same)
- **THEN** the system SHALL invoke `/bin/zsh -l -c 'command -v yt-dlp'` with a 3-second timeout
- **AND** the resulting absolute path SHALL be used for subsequent version queries and upgrade execution
- **AND** the upgrade subprocess SHALL be invoked using the absolute binary path directly, NOT wrapped in `zsh -l -c`

#### Scenario: User shell is bash or fish

- **WHEN** the user's login shell (per `$SHELL` / `pw_shell`) is `/bin/bash`, `/usr/local/bin/fish`, or `/opt/homebrew/bin/fish`
- **THEN** the discovery invocation SHALL use that shell with `-l -c 'command -v yt-dlp'`
- **AND** the same absolute-path policy SHALL apply for subsequent invocations

#### Scenario: User shell is unrecognized

- **WHEN** the user's login shell is not in the allowlist `{/bin/zsh, /bin/bash, /usr/local/bin/fish, /opt/homebrew/bin/fish, /bin/sh}`
- **THEN** the system SHALL fall back to `/bin/sh -l -c 'command -v yt-dlp'`

#### Scenario: Login-shell discovery also fails

- **WHEN** the login-shell discovery returns empty output or exits non-zero
- **THEN** the install method SHALL be classified as `missing`

### Requirement: Manual update action triggers a fresh version check

The system SHALL re-query the PyPI JSON API when the user clicks the update action button, rather than reusing the launch-time check result. This ensures the user sees the truly latest state at the moment of action.

#### Scenario: User clicks the action button when status bar shows "Up to date"

- **WHEN** the action button is clicked and the launch-time check showed up-to-date
- **THEN** the system SHALL re-query PyPI for the latest version
- **AND** if a new release has appeared since launch, the upgrade flow SHALL proceed using the install-method-appropriate command
- **AND** if the installed version is still current, the Output Log SHALL receive an info-level entry `yt-dlp is already up to date (latest: <version>)`

#### Scenario: User clicks the action button when status bar shows "Update available"

- **WHEN** the action button is clicked and the status bar shows an update is available
- **THEN** the system SHALL re-query PyPI for the latest version
- **AND** SHALL run the install-method-appropriate upgrade command using the latest result from this fresh query
