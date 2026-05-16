# Changelog

All notable changes to the PowerHour Video Generator GUI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING (legal):** Relicensed from MIT to GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). The AGPL is a strong-copyleft license: in addition to the GPLv3 obligations (source disclosure on distribution, same-license derivatives), it requires source disclosure when the software is used over a network. Forks, modified versions, and hosted deployments must make corresponding source available. Contributions accepted before this commit remain available under MIT in the git history; all new code and contributions are AGPL-3.0-or-later. See [LICENSE](../LICENSE) for the full text.

### Added
- yt-dlp version display and in-app update button to the existing GUI status bar. On launch, the GUI queries PyPI in a background thread for the latest stable release and indicates whether the local install is current. Supports auto-upgrade for Homebrew, pipx, pip (verified venv), Chocolatey, and standalone installs; shows a copy-paste manual command for unsupported managers (apt/dnf, conda, pyenv/asdf/mise shims, nix, snap, flatpak, scoop, winget, npm).

### Fixed
- Overall progress bar now scales to the actual video count instead of always assuming 60 (label was correct but the bar visually under-filled when fewer than 60 videos were processed).

## [1.0.0] - 2024-12-XX

### 🎉 Initial GUI Release

This is the first official release of the PowerHour Video Generator with a graphical user interface, migrating from the original command-line tool to a full-featured GUI application.

### Added

#### Core Features
- ✅ **Graphical User Interface** - Complete Tkinter-based GUI replacing command-line interface
- ✅ **Real-time Progress Tracking** - Live progress bars with ETA calculation
- ✅ **Threaded Processing** - Non-blocking UI during video processing
- ✅ **Input Validation** - Real-time validation with visual feedback
- ✅ **Configuration Persistence** - Settings saved between sessions
- ✅ **Recent Items** - Quick access to previously used files and folders

#### User Interface Components
- ✅ **Input Parameters Section** - Video source, common clip, fade duration, output file
- ✅ **Control Panel** - Start/Cancel buttons with status display
- ✅ **Progress Section** - Dual progress bars (current video and overall)
- ✅ **Output Log** - Color-coded logging with auto-scroll
- ✅ **Status Bar** - Resource monitoring and contextual hints

#### Advanced Features
- ✅ **Menu System** - Options and Help menus
- ✅ **Quality Settings** - Low/Medium/High presets
- ✅ **Audio Normalization** - Consistent volume across clips
- ✅ **Output Format Selection** - MP4/AVI/MKV support
- ✅ **Expert Mode** - Advanced FFmpeg parameter control
- ✅ **Preset System** - Save and load custom configurations

#### Processing Enhancements
- ✅ **URL Support** - Download from YouTube and other platforms
- ✅ **Automatic Loudness Analysis** - For proper audio normalization
- ✅ **Fade Effects** - Smooth transitions between clips
- ✅ **Random Clip Selection** - From videos longer than needed
- ✅ **Batch Processing** - Handle 60+ videos automatically

#### Error Handling & Recovery
- ✅ **Global Exception Handler** - Catches and logs all errors
- ✅ **User-Friendly Error Messages** - Technical errors mapped to clear explanations
- ✅ **Automatic Cleanup** - Temporary files removed on exit/error
- ✅ **Error Logging** - Detailed logs for troubleshooting
- ✅ **Validation Tooltips** - Helpful hints for input errors

#### Documentation
- ✅ **Module Documentation** - Comprehensive docstrings with type hints
- ✅ **README_GUI.md** - Installation and quick start guide
- ✅ **USER_GUIDE.md** - Detailed user documentation
- ✅ **CONTRIBUTING.md** - Developer guidelines
- ✅ **ARCHITECTURE.md** - System design documentation
- ✅ **CHANGELOG.md** - Version history (this file)

### Changed

#### From Command-Line to GUI
- 🔄 **Interface** - Migrated from CLI arguments to graphical controls
- 🔄 **Feedback** - Changed from console output to visual progress bars
- 🔄 **Configuration** - Moved from command-line flags to persistent settings
- 🔄 **Error Handling** - Enhanced with dialogs instead of console errors
- 🔄 **Processing** - Now runs in separate thread for responsiveness

#### Code Structure
- 🔄 **Architecture** - Separated GUI (`powerhour_gui.py`) from processing (`powerhour_processor.py`)
- 🔄 **Communication** - Queue-based messaging between threads
- 🔄 **Configuration** - JSON-based settings with OS-specific paths
- 🔄 **Validation** - Real-time with visual indicators
- 🔄 **Logging** - Multi-level with color coding

### Technical Details

#### Dependencies
- Python 3.8+
- Tkinter (built-in)
- FFmpeg (external)
- yt-dlp (optional)
- psutil (optional)

#### Platform Support
- Windows 10+
- macOS 10.14+
- Linux (Ubuntu 18.04+)

#### Performance
- Processing: 10-30 minutes for 60 videos
- Memory usage: 2-4 GB typical
- CPU usage: 50-100% during encoding
- Disk space: 5-10 GB recommended

---

## [0.9.0] - 2024-11-XX (Pre-release)

### Beta Testing Phase

### Added
- Initial GUI implementation
- Basic video processing
- Progress tracking

### Fixed
- Thread synchronization issues
- Memory leaks during processing
- Validation edge cases

### Known Issues
- Some tooltips may not appear
- Expert mode needs refinement
- Preset system incomplete

---

## [0.1.0] - 2024-10-XX (Original CLI)

### Original Command-Line Version

### Features
- Command-line interface
- Basic video processing
- FFmpeg integration
- Playlist download support

### Limitations
- No visual feedback
- No progress tracking
- No configuration persistence
- Command-line only

---

## Migration Guide

### From CLI (0.1.0) to GUI (1.0.0)

#### For Users
1. **Installation**: No change - same Python and FFmpeg requirements
2. **Usage**: Run `python powerhour_gui.py` instead of `python powerhour_generator.py`
3. **Features**: All CLI features available plus many more
4. **Configuration**: Now saved automatically

#### For Developers
1. **Architecture**: Code split into GUI and processor modules
2. **Threading**: Processing now runs in separate thread
3. **Communication**: Queue-based message passing
4. **Testing**: New test_gui.py for interface testing

---

## Roadmap

### Version 1.1.0 (Planned)
- [ ] Batch processing queue
- [ ] Video preview thumbnails
- [ ] Custom transitions per segment
- [ ] Pause/Resume capability

### Version 1.2.0 (Future)
- [ ] Audio-only mode
- [ ] Direct upload to YouTube/cloud
- [ ] Multi-language support
- [ ] Dark mode theme

### Version 2.0.0 (Long-term)
- [ ] Complete rewrite in modern framework
- [ ] Web-based interface option
- [ ] Distributed processing
- [ ] Plugin system

---

## Version Numbering

This project uses Semantic Versioning:
- **Major version (X.0.0)**: Incompatible API changes
- **Minor version (0.X.0)**: New functionality, backwards compatible
- **Patch version (0.0.X)**: Bug fixes, backwards compatible

## Support

For issues, feature requests, or questions:
1. Check the USER_GUIDE.md
2. Review error logs
3. Search existing issues
4. Create new issue with details

---

*PowerHour Video Generator - Changelog*  
*Maintained by: Anthony Izzo*
*Last Updated: 2024*