# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python Tkinter desktop app that builds "PowerHour" videos by sampling 60-second clips from a local folder or a YouTube playlist, interleaving a common transition clip, and concatenating into one output. Also has a CLI variant for scripting. Heavy use of `ffmpeg`/`ffprobe` subprocesses for analysis, normalization, and encoding; `yt-dlp` for downloads.

## Commands

The repo is `make`-driven. Common targets:

| Command | Purpose |
|---|---|
| `make install-dev` | Install dev deps (`requirements-dev.txt`: pytest, pyinstaller, flake8, black, mypy, etc.) |
| `make test` | Full test suite with coverage |
| `make run-gui` | Launch GUI via `python -m powerhour.powerhour_gui` |
| `make run-cli` | Launch CLI via `python -m powerhour.powerhour_generator` |
| `make lint` | flake8 + pylint + mypy (line length 120, ignores E203/W503) |
| `make format` | black + isort (line length 120) |
| `make build` / `make build-exe` | PyInstaller frozen build via `powerhour.spec` |
| `make check-deps` | Verify Python / ffmpeg / yt-dlp are reachable |

### Running the GUI for live debugging

Prefer `python powerhour/run_gui_debug.py` over `make run-gui` when investigating crashes — it prints step-by-step startup info and falls back to a full traceback if `__init__` raises.

### Running a single test

```
python -m pytest tests/test_ytdlp_updater.py::TestClassifyInstallMethod -v
python -m pytest tests/test_ytdlp_updater.py::TestCompareVersions::test_cases -v
```

`tests/test_gui.py` is a legacy manual-runner script (uses `print`, returns booleans); pytest picks it up but it doesn't follow the modern fixture pattern. New tests should use pytest-style classes/functions like `test_ytdlp_updater.py`.

## Architecture

### Thread + queue pattern (the load-bearing one)

Worker threads communicate with the Tk main loop through a shared `queue.Queue` (`self.message_queue`). The main loop polls it every 100ms via `PowerHourGUI.process_queue()` which reschedules itself with `self.after(100, self.process_queue)`. Any new background work should follow this pattern — never call Tk widget methods from a non-main thread.

Two workers live in their own modules:

- `powerhour/powerhour_processor.py` — `ProcessorThread`: video analysis, loudness normalization, re-encoding, concatenation. Emits message types: `progress`, `status`, `log`, `video_progress`, `complete`, `error`.
- `powerhour/ytdlp_updater.py` — `YtDlpUpdaterThread`: discovers yt-dlp, classifies its install method, queries PyPI, runs upgrade commands. Emits ONLY: `ytdlp_status`, `ytdlp_update_complete`, `log`.

### CRITICAL: `error` is destructive

`process_queue`'s `error` branch shows a "Processing Error" dialog, sets status to "Error", calls `reset_ui_state()`, and runs `cleanup_temp_files()`. **Any worker that emits `error` triggers all of that.** When adding a new worker, namespace its failure types (e.g., `myworker_error`) and add a dedicated handler in `process_queue`. The yt-dlp updater enforces this contract with a unit test (`test_check_only_emits_only_status` etc.) — keep similar coverage for any new worker.

### Status bar is shared, not owned per-feature

`PowerHourGUI.build_status_bar()` at `powerhour/powerhour_gui.py:457` already contains the resource-usage poller, hint/operation labels, and the yt-dlp section. Don't add a second status bar; extend this one and preserve existing widgets (`hint_label`, `operation_label`, `resource_label`, `update_resource_usage()`'s 2-second `after` rescheduling).

### yt-dlp install-method classification

`ytdlp_updater.classify_install_method()` runs ordered path-pattern tests against the casefolded realpath. Order matters — managed-manager paths (pipx → brew → choco → distro/shims/sandboxes → conda) MUST be checked before pip-via-shebang detection, otherwise a conda env's `yt-dlp` (whose shebang resolves to a real Python that owns the module) gets falsely classified as `pip`. Conda specifically requires both `conda-meta/` AND a `yt-dlp-*.json` marker — bare `conda-meta/` presence falls through to pip because that's the very common "`pip install yt-dlp` into a conda env" case.

If you add a new install-method, add the pattern in the correct slot and add tests under `TestClassifyInstallMethod` covering both the positive case and adversarial cases that might match an earlier or later rule.

### macOS frozen-`.app` PATH gap

`.app` bundles launched from Finder don't inherit shell PATH, so `shutil.which()` misses brew/pipx. `ytdlp_updater._login_shell_discover()` handles this by invoking the user's login shell (from `$SHELL` or `pwd.getpwuid`, against an allowlist) with `-l -c 'command -v <target>'`, **only for discovery**. Subsequent subprocess calls use the absolute path directly — never wrap the upgrade command in a shell.

### Module boundary discipline

`powerhour_gui.py` is ~2700 lines and growing past the comfortable refactor threshold. New non-trivial worker logic should land in a sibling module (model: `ytdlp_updater.py`) and communicate with the GUI exclusively through the message queue. The GUI module imports the worker class and instantiates it; it should never contain the worker's internal logic.

## Workflow notes

- **OpenSpec is supported but gitignored.** `openspec/` is in `.gitignore`; proposals/designs/specs/tasks are contributor-local. Running `openspec list/status/archive` still works locally. Don't commit the `openspec/` tree.
- **`__version__`** at `powerhour/__init__.py` is the single source of truth for the project version. `setup.py`, `scripts/build.py`, `powerhour.spec` (including the macOS `CFBundleShortVersionString` / `CFBundleVersion` keys), and `Makefile` all derive from it via a build-time regex parse — do not edit them independently. `ytdlp_updater.USER_AGENT` also pulls from it at import time. When cutting a release, edit `__version__` and `docs/CHANGELOG.md`; everything else picks it up automatically.
- **In-app help strings are documentation.** Dialog bodies (`messagebox.showinfo`/`showerror`), tooltips, status-bar hints, and error messages are subject to the same verification discipline as `docs/*.md`. If a string claims a behavior, the behavior must be implemented. The `Help → Keyboard Shortcuts` dialog was removed in 1.1.0 specifically because it enumerated shortcuts that were never bound; don't reintroduce the menu item without binding the shortcuts.
- **Logging into the Output Log panel.** Workers emit `{'type': 'log', 'level': 'info|warning|error', 'message': '...'}`. The GUI routes through `log_info`/`log_warning`/`log_error` to the `ScrolledText` widget at `powerhour_gui.py:627` with color-coded tags.

## Keeping documentation in sync

Every change ships its own documentation update in the same commit/PR. Three layers, three thresholds:

- **`docs/CHANGELOG.md` — update on every change**, no exceptions. Add an entry under `## [Unreleased]` (create that section if absent). Use one of the existing categories: Added / Changed / Fixed / Removed / Deprecated / Security. Bug fixes and refactors count; "no user-visible change" still goes under Changed/Fixed with a one-liner. Roll `[Unreleased]` into a numbered release section when cutting a version.
- **`README.md` — update on substantial changes.** Substantial means anything that alters: what the project does, how it's invoked, its dependency or system requirements, or its install/uninstall story. New features, new CLI flags, new optional integrations, and breaking changes all qualify. Pure bug fixes and internal refactors do not.
- **Other `docs/` files — update when their topic is touched.** The doc surface is exactly four files; each owns a disjoint scope:
  - `docs/USER_GUIDE.md` — end-user comprehensive guide: per-OS install (Python, FFmpeg, yt-dlp), GUI walkthrough, CLI reference, configuration schema, troubleshooting, FAQ
  - `docs/DEVELOPING.md` — contributor onboarding and high-level architecture overview; links into this file (CLAUDE.md) for code-touching specifics
  - `docs/CHANGELOG.md` — version history (Keep-a-Changelog format)
  - `docs/RELEASE.md` — maintainer release procedure

If a change touches the GUI flow, check `USER_GUIDE.md`. If it touches the threading/queue model or module layout, the human-facing reference is `DEVELOPING.md` and the authoritative reference is this file — keep both in sync. If you can't honestly say "the docs still describe the code accurately" after your change, the change isn't done.

## Things to know before editing

- Test framework is **pytest**. The GUI smoke tests in `tests/test_ytdlp_updater.py` skip cleanly when no display is available — keep that skip guard if you add similar tests.
- Line length is **120** (not 80). Black/flake8/mypy/pylint all configured around that.
- The processor's `_download_playlist` at `powerhour_processor.py:264` has known signal-loss issues (stderr redirected to a soon-deleted temp file, stdout filtered to `[download]` lines only, no `--newline` flag for yt-dlp). Fixing those is a separate scoped change; don't bundle it into unrelated work.
