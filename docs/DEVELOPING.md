# Developing PowerHour Generator

Contributor onboarding and high-level architecture overview.

> **Source of truth for code-touching specifics is [`/CLAUDE.md`](../CLAUDE.md)** (also available as [`/AGENTS.md`](../AGENTS.md) — they're byte-identical). The queue message-type list, the `error`-is-destructive contract, the install-method classification ordering rule, the macOS frozen-`.app` PATH gap, the `_download_playlist` known issues, and the module-boundary discipline all live there. This doc links into it rather than paraphrasing it, because paraphrases drift independently of the source.

## Quick setup

```bash
git clone https://github.com/izzoa/powerhour-generator.git
cd powerhour-generator
make install-dev      # installs everything from requirements-dev.txt
make check-deps       # verifies Python, ffmpeg, ffprobe, yt-dlp are reachable
```

`requirements-dev.txt` brings in pytest, pyinstaller, flake8, black, mypy, pylint, isort, sphinx, twine, ipython, and yt-dlp (for download testing).

## Running things

```bash
make run-gui          # python -m powerhour.powerhour_gui
make run-cli          # python -m powerhour.powerhour_generator
make test             # pytest with coverage
make lint             # flake8 + pylint + mypy (120-char line length)
make format           # black + isort (120-char line length)
make build-exe        # PyInstaller frozen build via powerhour.spec
make ci               # local equivalent of the CI pipeline
make check-deps       # confirm runtime tools are on PATH
```

When the GUI crashes on startup and `make run-gui` gives you nothing useful, run `python powerhour/run_gui_debug.py` instead — it prints step-by-step startup info and surfaces full tracebacks if `__init__` raises (see [CLAUDE.md § Running the GUI for live debugging](../CLAUDE.md#running-the-gui-for-live-debugging)).

### Single tests

```bash
python -m pytest tests/test_ytdlp_updater.py::TestClassifyInstallMethod -v
python -m pytest tests/test_ytdlp_updater.py::TestCompareVersions::test_cases -v
```

`tests/test_ytdlp_updater.py` is the modern pytest-style suite and is the model to follow for new tests. `tests/test_gui.py` is a legacy manual-runner script; pytest picks it up but its style isn't the one to copy (see [CLAUDE.md § Running a single test](../CLAUDE.md#running-a-single-test)).

## Project layout

```
powerhour-generator/
├── powerhour/                  # source package
│   ├── __init__.py             # exports + __version__ (canonical version source)
│   ├── powerhour_gui.py        # Tkinter GUI (~2,700 lines)
│   ├── powerhour_processor.py  # ProcessorThread: scan, loudnorm, encode, concat
│   ├── powerhour_generator.py  # CLI entry point
│   ├── ytdlp_updater.py        # YtDlpUpdaterThread: discover, classify, upgrade yt-dlp
│   └── run_gui_debug.py        # verbose-startup launcher for crash diagnosis
├── tests/                      # pytest test suite
│   ├── test_ytdlp_updater.py   # modern pytest suite (model for new tests)
│   └── test_gui.py             # legacy manual-runner script
├── docs/                       # user-facing documentation (this directory)
├── scripts/                    # build automation + per-OS install scripts
│   ├── build.py
│   ├── install_requirements_mac.sh
│   ├── install_requirements_deb.sh
│   └── Install_Requirements_Win.ps1
├── assets/                     # logo and other static assets
├── .github/
│   ├── workflows/              # CI and release pipelines
│   └── CONTRIBUTING.md         # one-line redirect to this file
├── CLAUDE.md / AGENTS.md       # code-touching reference (source of truth)
├── Makefile                    # all dev workflow targets
├── setup.py                    # package config (reads version from __init__.py)
├── powerhour.spec              # PyInstaller spec
├── requirements.txt            # runtime deps (Pillow, pyperclip)
└── requirements-dev.txt        # dev deps
```

Module boundary rules (when to split a new module vs. extend an existing one) are in [CLAUDE.md § Module boundary discipline](../CLAUDE.md#module-boundary-discipline).

## Architecture in one paragraph

The GUI runs on Tk's main loop. Long-running work (video processing, yt-dlp downloads, PyPI queries) runs in worker threads that communicate back to the main loop through a shared `queue.Queue` (`self.message_queue`), which the main loop polls every 100 ms via `process_queue()`. Worker threads never touch Tk widgets directly — they emit typed messages and the main loop interprets them. For the full message-type list, the threading rules, and the **critical** `error`-is-destructive contract that any new worker must respect, see [CLAUDE.md § Thread + queue pattern](../CLAUDE.md#thread--queue-pattern-the-load-bearing-one) and [CLAUDE.md § CRITICAL: `error` is destructive](../CLAUDE.md#critical-error-is-destructive).

### Worker modules

**`powerhour/powerhour_processor.py`** — the `ProcessorThread` class. Validates inputs, downloads the playlist if needed, scans for videos ≥80 seconds, measures loudness with FFmpeg's `loudnorm` filter, re-encodes a random 60-second window from each at 1280×720 with the measured loudness applied, and concatenates with the common transition clip interleaved. Known signal-loss issues in `_download_playlist` are documented in [CLAUDE.md § Things to know before editing](../CLAUDE.md#things-to-know-before-editing).

**`powerhour/ytdlp_updater.py`** — the `YtDlpUpdaterThread` class plus its support functions. Discovers the installed `yt-dlp` binary (with a login-shell fallback for macOS frozen-`.app` launches that don't inherit shell PATH — see [CLAUDE.md § macOS frozen-.app PATH gap](../CLAUDE.md#macos-frozen-app-path-gap)), classifies its install method by path pattern (ordering matters — see [CLAUDE.md § yt-dlp install-method classification](../CLAUDE.md#yt-dlp-install-method-classification)), queries PyPI for the latest stable, and orchestrates upgrades for the install methods it can safely manage.

### Status bar is shared

The bottom status bar at `powerhour_gui.py:457` is shared by the resource-usage poller, the hint/operation labels, and the yt-dlp section. Don't add a second status bar — extend this one and preserve the existing widgets (see [CLAUDE.md § Status bar is shared, not owned per-feature](../CLAUDE.md#status-bar-is-shared-not-owned-per-feature)).

## Version is single-sourced

The string in `powerhour/__init__.py:__version__` is canonical. `setup.py`, `scripts/build.py`, `powerhour.spec`, and the `Makefile` all derive from it (via a small regex parse of `__init__.py` at build time — they don't `import powerhour`, to avoid pulling Tk into the build). When you bump a release, edit `__version__` and `docs/CHANGELOG.md`; everything else picks it up automatically.

`ytdlp_updater.USER_AGENT` also pulls from `__version__` at import time, so the version that appears in PyPI request headers stays aligned.

## Contributing

The workflow is standard GitHub PRs:

1. Fork the repo and create a feature branch from `main`.
2. Make your change. Keep commits focused — one logical change per commit is easier to review.
3. Run `make ci` locally to confirm tests and lints pass with the same checks CI runs.
4. Push your branch and open a PR against `main`.

Commit messages: short, descriptive, present tense ("Add X", "Fix Y", "Update Z"). Conventional Commits style (`fix:`, `feat:`, `docs:`) is welcome but not required. The repo's existing history is mixed.

### Documentation sync

Every change ships its own documentation update in the same commit/PR. The thresholds are spelled out in [CLAUDE.md § Keeping documentation in sync](../CLAUDE.md#keeping-documentation-in-sync) — the short version: `docs/CHANGELOG.md` for every change without exception; `README.md` for substantial user-visible changes; topic-specific docs (`USER_GUIDE.md`, `DEVELOPING.md`, `RELEASE.md`) when their area is touched.

In-app help text counts as documentation. If you add a dialog, error message, status hint, or messagebox that claims a behavior, the behavior must actually be implemented and the same verification discipline as written docs applies.

### Code style

- Line length is **120**, not 80. Black, flake8, mypy, and pylint are all configured around that.
- Type hints on new functions and methods.
- Docstrings on classes and public methods. Don't over-document obvious helpers.
- Never call Tk widget methods from a non-main thread. See the queue pattern in CLAUDE.md.

## OpenSpec workflow

Substantial changes (anything affecting multiple files, requiring design discussion, or shipping new capabilities) are tracked as OpenSpec proposals in `openspec/changes/<change-name>/`. The directory is gitignored — proposals, designs, specs, and tasks are contributor-local. Running `openspec list/status/archive` still works locally; nothing about OpenSpec needs to be committed.

If you're not familiar with OpenSpec, you can skip it for small changes. Larger work benefits from the structure (proposal → design → spec → tasks → implementation), and Claude Code has slash commands (`/opsx:propose`, `/opsx:apply`, `/opsx:archive`) for driving it.

## Building releases

The maintainer-only release procedure (tagging, building artifacts, PyPI uploads, post-release verification) is in [RELEASE.md](RELEASE.md).
