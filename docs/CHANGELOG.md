# Changelog

All notable changes to PowerHour Generator are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

<!-- Add entries here as changes land. Roll into a numbered release when cutting a version. -->

## [1.1.0] - 2026-05-16

### Changed
- **BREAKING (legal):** Relicensed from MIT to GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). The AGPL is a strong-copyleft license: in addition to GPLv3 obligations (source disclosure on distribution, same-license derivatives), it requires source disclosure when the software is used over a network. Forks, modified versions, and hosted deployments must make corresponding source available. Contributions accepted before this commit remain available under MIT in the git history; all new code and contributions are AGPL-3.0-or-later. See [LICENSE](../LICENSE) for the full text.
- **Documentation revamp.** Consolidated `docs/` from seven files to four. `README_GUI.md`, `CONTRIBUTING.md`, `PROJECT_STRUCTURE.md`, and `ARCHITECTURE.md` are removed; their non-duplicative content merged into `USER_GUIDE.md` and a new `DEVELOPING.md`. `README.md` rewritten as a landing page that links out to deeper docs instead of duplicating them. `DEVELOPING.md` defers code-touching specifics (queue contract, install-method classification, threading discipline) to `CLAUDE.md`/`AGENTS.md` as source of truth. Every concrete claim in the new docs verified against the code; fabricated content (a nonexistent keyboard-shortcut table, a "drag-and-drop" feature, speculative roadmap entries) removed.
- **Version is now single-sourced** from `powerhour/__init__.py:__version__`. `setup.py`, `scripts/build.py`, `powerhour.spec`, and `Makefile` derive their version strings from it via build-time regex parse instead of carrying independent hardcoded copies.

### Added
- **yt-dlp version display and in-app update button** in the GUI status bar. On launch, the GUI queries PyPI in a background thread for the latest stable release and shows whether the local install is current. Supports auto-upgrade for Homebrew, pipx, pip-in-venv, Chocolatey, and standalone installs; shows a copy-paste manual command for unsupported managers (apt/dnf, conda, pyenv/asdf/mise shims, nix, snap, flatpak, scoop, winget, npm).
- `.github/CONTRIBUTING.md` redirect stub for GitHub-native contributor discoverability.

### Fixed
- Overall progress bar now scales to the actual video count instead of always assuming 60 (the label was correct but the bar visually under-filled when fewer than 60 videos were processed).
- **`Help → Keyboard Shortcuts` dialog removed** — it was lying. The dialog enumerated `Ctrl+O`/`Ctrl+S`/`Ctrl+R`/`Ctrl+Q`/`F11` as bound shortcuts, but none of them were ever bound. The menu item and `show_shortcuts()` function are both removed. If keyboard shortcuts are wired up in a future release, both come back together.
- **`Help → Check for Updates` removed** — it never actually checked anything, just showed a static "you are running the latest version" message that was both useless and incorrect after any release.

## [1.0.0] - 2025-09-05

### Initial GUI release

Migrated from CLI-only to a full Tkinter GUI application while keeping the CLI script intact for scripting use.

### Added
- Tkinter GUI with input parameters, control panel, progress bars, output log, and status bar.
- Worker-thread + queue architecture so the UI stays responsive during processing.
- Real-time progress tracking with ETA and per-clip/overall progress bars.
- Input validation with visual feedback (green/red borders) on the source, common-clip, fade, and output fields.
- JSON configuration persistence under OS-appropriate paths (`%APPDATA%/PowerHour/`, `~/Library/Application Support/PowerHour/`, `~/.config/PowerHour/`).
- Recent-items dropdowns for source folders, common clips, and output paths.
- Menu system with Options (quality/normalization/format/presets/expert mode) and Help (about/user guide/error log).
- Preset system with three built-ins (Quick Party Mix, High Quality Archive, Fast Processing) and save/load for custom presets.
- Expert mode for editing FFmpeg parameters directly.
- Color-coded log panel with info/warning/error tagging.
- Resource-usage display in the status bar (CPU + RAM via `psutil`, if installed).
- Cross-platform package structure: source under `powerhour/`, tests under `tests/`, docs under `docs/`, scripts under `scripts/`.
- PyInstaller `.spec` for frozen builds.
- Make-driven dev workflow (`make test`, `make lint`, `make format`, `make build-exe`, etc.).

### Changed
- Project reorganized into a proper Python package. Old `powerhour_gui.py` / `powerhour_processor.py` at root replaced by `powerhour/powerhour_gui.py` / `powerhour/powerhour_processor.py`; invocation is now `python -m powerhour.powerhour_gui` instead of `python powerhour_gui.py`.

## [0.1.0] - 2024-02-03

### Initial CLI release

The original command-line tool that started the project. Accepts a source folder or playlist URL, a common transition clip, a fade duration, and an output filename; produces a one-hour PowerHour video.

### Added
- `powerhour_generator.py` CLI script with four positional arguments.
- FFmpeg-based loudness analysis (`loudnorm`) and re-encoding.
- yt-dlp integration for downloading YouTube playlists.
- Per-OS install scripts under `scripts/`.
