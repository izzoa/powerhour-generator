# PowerHour Generator — User Guide

Comprehensive guide to installing PowerHour Generator and using it to make hour-long party videos. If you just want to clone-and-run, the [project README](../README.md) has a 60-second quickstart; this is the long form.

## What is a PowerHour?

A PowerHour is a party game where players take a sip of beer every minute for an hour, traditionally accompanied by a video that changes every 60 seconds. This tool builds that video for you: it takes a folder of videos (or a YouTube playlist), samples a random 60-second clip from each, sandwiches a short transition clip between them, normalizes the audio so no clip blows out anyone's ears, and stitches the whole thing into a single hour-long MP4.

## Contents

- [Install](#install)
- [Running the GUI](#running-the-gui)
- [Running the CLI](#running-the-cli)
- [Configuration](#configuration)
- [Keeping yt-dlp up to date](#keeping-yt-dlp-up-to-date)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Install

PowerHour Generator runs on Windows 10+, macOS 10.13+, and Linux (Ubuntu 18.04+ and equivalents). CI exercises Python 3.8–3.11 on all three platforms.

### 1. Python 3.8 or newer

- **Windows:** download from [python.org](https://www.python.org/downloads/) and tick "Add Python to PATH" during install.
- **macOS:** `brew install python3`
- **Linux (Debian/Ubuntu):** `sudo apt install python3 python3-pip`

Verify: `python3 --version` should print 3.8 or higher.

### 2. FFmpeg

FFmpeg is the engine that does the actual video work. It must be on your `PATH`.

- **Windows:** download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add the `bin` directory to your system PATH.
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

Verify: `ffmpeg -version` and `ffprobe -version` should both print version info.

### 3. PowerHour Generator itself

```bash
git clone https://github.com/izzoa/powerhour-generator.git
cd powerhour-generator
pip install -r requirements.txt
```

The required deps are `Pillow` and `pyperclip`; both come from PyPI.

### 4. yt-dlp (optional, for YouTube playlist URLs)

Only needed if you're going to point the source field at a YouTube/playlist URL instead of a local folder. The GUI's status bar shows the installed version and can update it for you, but you need at least one initial install. Pick the method that matches your environment:

| Platform | Command |
|---|---|
| macOS (Homebrew) | `brew install yt-dlp` |
| Linux (apt) | `sudo apt install yt-dlp` *(often lags upstream — pipx is better)* |
| Windows (Chocolatey) | `choco install yt-dlp` |
| Cross-platform (pipx, recommended) | `pipx install yt-dlp` |
| Standalone binary | grab from the [yt-dlp releases page](https://github.com/yt-dlp/yt-dlp/releases) and put on PATH |

The GUI's in-app updater knows how to upgrade Homebrew, pipx, pip-in-venv, Chocolatey, and standalone-binary installs automatically. For others (apt, conda, asdf/pyenv/mise shims, snap, flatpak, scoop, winget, npm, etc.) it shows you the right command to run instead of guessing.

### Quick verification

```bash
python3 --version       # 3.8 or higher
ffmpeg -version         # any recent version
ffprobe -version
yt-dlp --version        # only if you installed yt-dlp
```

## Running the GUI

```bash
python -m powerhour.powerhour_gui
# or, if you cloned the repo and have make:
make run-gui
```

The window is divided into five regions:

1. **Input parameters** (top) — Video source field (folder path or playlist URL), Common Clip field (path to your transition video), Fade Duration spinner, Output File field.
2. **Control panel** — Start Processing (green) and Cancel (red) buttons, plus a status label.
3. **Progress** — Current-video progress bar, overall progress bar, ETA and processing-speed indicators.
4. **Output log** — Color-coded log of what's happening (info in black, warnings in orange, errors in red).
5. **Status bar** (bottom) — Contextual hint, current operation, CPU/RAM usage (if `psutil` is installed), and the yt-dlp version/update controls.

A typical run:

1. Click **Browse** next to Video Source and pick a folder of videos (or paste a YouTube playlist URL into the field).
2. Click **Browse** next to Common Clip and pick a short transition video (3–5 seconds works well).
3. Set fade duration (default 3.0 seconds is fine for most cases).
4. Click **Save As** next to Output File to pick where the final MP4 lands.
5. Click **Start Processing**.

Processing takes roughly 10–30 minutes depending on your machine, your source video sizes, and the quality preset. The output log shows what FFmpeg is doing if you want to follow along.

The menu bar has two top-level menus:

- **Options** — Video Quality (Low/Medium/High = CRF 28/23/18), Audio Normalization toggle, Output Format (MP4/AVI/MKV), Presets (save/load + three built-ins: Quick Party Mix, High Quality Archive, Fast Processing).
- **Help** — About PowerHour (version info), User Guide (built-in mini help), View Error Log (opens the log file in your OS default editor).

> Heads up: this version doesn't bind any keyboard shortcuts. Earlier docs claimed `Ctrl+O`/`Ctrl+R`/`F11` etc. were available — they weren't. If you want shortcuts wired up, that's a future change.

## Running the CLI

The CLI is a thin wrapper around the same processing engine, intended for scripts and CI. It takes four positional arguments and no flags.

```bash
python -m powerhour.powerhour_generator <source> <transition.mp4> <fade-seconds> <output.mp4>
```

| Position | Meaning |
|---|---|
| `<source>` | Path to a folder of videos, **or** a `http://`/`https://` URL pointing at a YouTube playlist |
| `<transition.mp4>` | Path to the short clip that plays between each video |
| `<fade-seconds>` | Crossfade duration on each clip, as a float (e.g., `3` or `2.5`) |
| `<output.mp4>` | Output filename (anything FFmpeg can write to) |

Examples:

```bash
# Local folder
python -m powerhour.powerhour_generator ./videos ./transition.mp4 3 powerhour.mp4

# YouTube playlist
python -m powerhour.powerhour_generator "https://youtube.com/playlist?list=..." ./transition.mp4 3 powerhour.mp4
```

When given a URL, the CLI downloads the playlist via `yt-dlp` into a temporary directory and processes it from there.

## Configuration

The GUI saves your settings between runs. The config file is JSON and lives at:

| OS | Path |
|---|---|
| Windows | `%APPDATA%\PowerHour\config.json` |
| macOS | `~/Library/Application Support/PowerHour/config.json` |
| Linux | `~/.config/PowerHour/config.json` |

The error log file lives alongside it as `error.log`.

Persisted keys:

- `window_geometry` — restored on next launch
- `last_video_source`, `last_common_clip`, `last_output_dir` — pre-fill the corresponding fields
- `default_fade_duration` — pre-fill the spinner (default `3.0`)
- `recent_sources`, `recent_common_clips`, `recent_outputs` — dropdown history (last `max_recent_items`, default 10)
- `max_recent_items` — cap on dropdown history
- `video_quality` — `"low"`, `"medium"`, or `"high"`
- `audio_normalization` — boolean
- `output_format` — `"mp4"`, `"avi"`, or `"mkv"`
- `expert_mode` — boolean
- `presets` — dictionary of named preset bundles

You can edit this file directly while the GUI is closed if you want.

## Keeping yt-dlp up to date

YouTube changes its internal extractors often, so a stale yt-dlp is the most common cause of "playlist URL failed to download." The GUI's status bar shows your installed version with a freshness indicator (`• Up to date` or `• Update available: X.Y.Z`) and a button next to it:

- **Update yt-dlp** — runs the upgrade command that matches your install method (Homebrew, pipx, pip-in-venv, Chocolatey, or replacing a standalone binary). Output streams into the log panel.
- **Check for Update** — re-queries PyPI when you're already current, in case a newer release dropped since launch.
- **How to install** — shown when yt-dlp isn't installed at all; opens the install instructions in your browser.

If the GUI detects an install method it can't safely upgrade (apt/dnf, conda, asdf/pyenv/mise shims, nix, snap, flatpak, scoop, winget, npm, etc.), it shows you a copy-paste command appropriate to that manager instead of running anything automatically.

Note for nightly-channel users: the launch-time check compares against PyPI's *stable* release. If your installed nightly is newer than PyPI's latest stable, the status bar will say "Up to date" — the GUI will not prompt you to downgrade.

## Troubleshooting

### "FFmpeg not found"
Verify with `ffmpeg -version` in a terminal. If that fails, FFmpeg either isn't installed or isn't on your `PATH`. Re-install per the [install section](#2-ffmpeg) and reopen the GUI.

### "No valid videos found"
The processor only keeps videos ≥80 seconds long (you need that extra 20 seconds so it can pick a random start point between 10 and `duration - 70` seconds). Drop shorter clips into the source folder or use longer source material. The processor scans everything in the folder *except* `.log`, `.py`, `.txt`, and `.json` files, so unusual video formats are fine as long as FFmpeg can decode them.

### Processing is slow
- Run it from a local SSD, not a network drive.
- Close other heavy apps while it runs (FFmpeg will happily eat all your cores).
- Use the **Low Quality** preset if you don't need broadcast quality.
- The processor needs roughly 5–10 GB of temp space; if your scratch disk is small or full, the bottleneck is I/O, not CPU.

### "Permission denied"
- **Windows:** run the terminal/GUI as administrator.
- **macOS/Linux:** check folder permissions with `ls -la`; `chmod` as needed.

### Output has no sound
Verify your source videos actually have audio (some YouTube-ripped clips don't). If they do, leave Audio Normalization enabled — the loudnorm filter is well-tested and shouldn't drop audio on its own.

### Application won't start
- Check `python --version` is 3.8+.
- Check Tkinter is available: `python -m tkinter` should open a small test window.
- If launching the GUI gives no visible error, try `python powerhour/run_gui_debug.py` instead — it prints step-by-step startup info.

## FAQ

**How long does processing take?** Usually 10–30 minutes for 60 videos. Depends on your CPU, quality preset, and source resolutions.

**Can I use videos shorter than 60 seconds?** No. The processor needs at least 80 seconds of source so it can pick a random 60-second window with a little headroom.

**What video formats are supported?** Anything FFmpeg can decode — MP4, MKV, MOV, AVI, WMV, FLV, WebM, and many more.

**Can I pause and resume processing?** Not currently. Cancel stops it cleanly; otherwise it runs to completion.

**How does audio normalization work?** The processor runs FFmpeg's `loudnorm` filter at I=-23 LUFS (broadcast standard), measures each clip's loudness once, then re-encodes the clip with the measured values applied for proper two-pass normalization.

**Can I change the output resolution?** Not from the GUI. It's hardcoded to 1280×720. You'd need to modify the `scale=1280:720` filter in `powerhour/powerhour_processor.py`.

**Is GPU acceleration supported?** Not by default. Expert users can modify the FFmpeg command in the processor to use hardware encoders (`h264_nvenc`, `h264_videotoolbox`, etc.) for their platform.

**Why do my outputs have black bars?** The processor scales everything to 1280×720. Anything that isn't 16:9 gets letterboxed.

**Why do some videos fail to process?** Usually codec or container issues. Check the output log for the specific FFmpeg error.

**What about more than 60 videos?** The processor randomly picks 60 from whatever's in your folder.

## License

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). See the [LICENSE](../LICENSE) file at the project root for the full text.
