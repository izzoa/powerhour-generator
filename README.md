# PowerHour Generator 🎉

> Make hour-long party videos by stitching together 60 one-minute clips. GUI and CLI included.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FFmpeg required](https://img.shields.io/badge/FFmpeg-required-green.svg)](https://ffmpeg.org/)
[![License: AGPL v3+](https://img.shields.io/badge/License-AGPL_v3+-blue.svg)](LICENSE)

PowerHour Generator takes a folder of videos (or a YouTube playlist URL), picks a random 60-second clip from each one, sandwiches a short transition clip between them, normalizes the audio, and concatenates the lot into a single hour-long MP4 you can drop into a party. There's a Tkinter GUI for clicking through the options and a CLI for scripting it.

## Quick start

You'll need Python 3.8+ and FFmpeg already installed. For the full per-OS install matrix (including yt-dlp for playlist URLs), see [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

```bash
git clone https://github.com/izzoa/powerhour-generator.git
cd powerhour-generator
python -m powerhour.powerhour_gui                # GUI
# or
python -m powerhour.powerhour_generator <source> <transition.mp4> <fade-seconds> <output.mp4>
```

`<source>` is either a folder of videos or a YouTube playlist URL. `<transition.mp4>` is the short clip (3–5 seconds works well) that plays between each main clip.

## For contributors

The repo is `make`-driven:

```bash
make install-dev        # dev deps (pytest, pyinstaller, lint, etc.)
make run-gui            # launch the GUI
make test               # run the test suite
make lint               # flake8 + pylint + mypy
make build-exe          # PyInstaller frozen build
```

See [docs/DEVELOPING.md](docs/DEVELOPING.md) for the full developer onboarding, and [CLAUDE.md](CLAUDE.md) (also available as [AGENTS.md](AGENTS.md)) for the code-touching reference both human contributors and AI agents pull from.

## Documentation

| Document | What's in it |
|---|---|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | End-user guide: install per OS, GUI walkthrough, CLI reference, troubleshooting, FAQ |
| [docs/DEVELOPING.md](docs/DEVELOPING.md) | Contributor onboarding and architecture overview |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |
| [docs/RELEASE.md](docs/RELEASE.md) | Maintainer release procedure |
| [CLAUDE.md](CLAUDE.md) / [AGENTS.md](AGENTS.md) | Source of truth for code-touching specifics (threading model, queue contract, install-method classification, module boundaries) |

## How it works (in one paragraph)

The processor scans your source folder (or downloads the playlist via yt-dlp), keeps any video ≥80 seconds, runs FFmpeg's `loudnorm` filter to measure each clip's loudness, picks a random 60-second window per video, re-encodes that window at 1280×720 with the measured loudness applied and crossfades at both ends, interleaves your common transition clip between each, and concatenates the result. Up to 60 source videos go into one hour of output.

## License

[GNU Affero General Public License v3.0 or later](LICENSE) (AGPL-3.0-or-later). The AGPL is a strong-copyleft license: in addition to the GPLv3 obligations (source disclosure on distribution, same-license derivatives), it requires source disclosure when the software is used over a network. Forks, modified versions, and hosted deployments must make corresponding source available. Contributions accepted before the relicense remain available under their original MIT terms in git history; new contributions are AGPL-3.0-or-later.

## Support

- Bug reports and feature requests: [GitHub Issues](https://github.com/izzoa/powerhour-generator/issues)
- Questions: [GitHub Discussions](https://github.com/izzoa/powerhour-generator/discussions)

Built with FFmpeg, Python, Tkinter, and yt-dlp. Pour responsibly.
