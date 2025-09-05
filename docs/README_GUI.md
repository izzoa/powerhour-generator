# PowerHour Video Generator GUI

A user-friendly graphical interface for creating PowerHour videos - hour-long compilations of 60 one-minute video clips with smooth transitions.

## Table of Contents
- [Installation](#installation)
- [System Requirements](#system-requirements)
- [Quick Start Guide](#quick-start-guide)
- [Features](#features)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

## Installation

### Prerequisites
1. **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
2. **FFmpeg** - Required for video processing
3. **yt-dlp** (optional) - For downloading online playlists

### Installing FFmpeg

#### Windows
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the archive to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify installation: `ffmpeg -version`

#### macOS
```bash
# Using Homebrew
brew install ffmpeg

# Verify installation
ffmpeg -version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

### Installing the PowerHour GUI

1. **Clone or download the repository:**
```bash
git clone https://github.com/izzoa/powerhour-generator.git
cd powerhour-generator
```

2. **Install Python dependencies:**
```bash
pip install tkinter
pip install psutil  # Optional: for resource monitoring
```

3. **Install yt-dlp (optional, for URL support):**
```bash
pip install yt-dlp
```

## System Requirements

### Minimum Requirements
- **OS:** Windows 10, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **CPU:** Dual-core processor (2.0 GHz+)
- **RAM:** 4 GB
- **Storage:** 10 GB free space
- **Python:** 3.8 or higher

### Recommended Requirements
- **CPU:** Quad-core processor (2.5 GHz+)
- **RAM:** 8 GB or more
- **Storage:** 20 GB free space
- **GPU:** Hardware encoding support (optional, improves speed)

## Quick Start Guide

### Step 1: Launch the Application
```bash
python powerhour_gui.py
```

### Step 2: Select Video Source
- **Local Folder:** Click "Browse" and select a folder containing video files
- **Online Playlist:** Paste a YouTube playlist URL directly

### Step 3: Choose Common Clip
Select a transition video that plays between each main clip (typically 3-5 seconds).

### Step 4: Configure Settings
- **Fade Duration:** Set transition smoothness (0-10 seconds)
- **Output File:** Choose where to save the final video

### Step 5: Start Processing
1. Click "Start Processing" (green button)
2. Monitor progress in real-time
3. Processing typically takes 10-30 minutes
4. Final video will be saved to your specified location

## Features

### Core Features
- ✅ **Intuitive GUI** - Easy-to-use interface for all skill levels
- ✅ **Video Source Flexibility** - Local folders or online playlists
- ✅ **Real-time Progress** - Track processing with ETA
- ✅ **Audio Normalization** - Consistent volume across all clips
- ✅ **Smooth Transitions** - Customizable fade effects
- ✅ **Threading** - Non-blocking UI during processing

### Advanced Features
- 🎯 **Preset System** - Save and load custom configurations
- 🎯 **Expert Mode** - Fine-tune FFmpeg parameters
- 🎯 **Recent Items** - Quick access to previous selections
- 🎯 **Resource Monitoring** - CPU and RAM usage display
- 🎯 **Error Recovery** - Automatic cleanup and detailed logging

### Configuration Persistence
- Window size and position
- Recent folders and files
- Quality settings
- User preferences

## Video Requirements

### Input Videos
- **Minimum Duration:** 80 seconds per video
- **Supported Formats:** MP4, AVI, MKV, MOV, and more
- **Recommended:** At least 60 videos for a full PowerHour

### Common Clip
- **Duration:** 3-5 seconds recommended
- **Purpose:** Transition between main clips
- **Format:** Any video format supported by FFmpeg

### Output
- **Duration:** ~60 minutes (60 one-minute clips + transitions)
- **Format:** MP4 (recommended), AVI, or MKV
- **Resolution:** 1280x720 (HD)
- **Frame Rate:** 30 fps

## Troubleshooting

### Common Issues

#### "FFmpeg not found"
- **Solution:** Ensure FFmpeg is installed and in your system PATH
- **Verify:** Run `ffmpeg -version` in terminal

#### "No valid videos found"
- **Issue:** Videos must be at least 80 seconds long
- **Solution:** Use longer video files

#### "Permission denied" errors
- **Windows:** Run as administrator
- **macOS/Linux:** Check folder permissions

#### Processing is slow
- **Tips:**
  - Close other applications
  - Use "Low Quality" preset for faster processing
  - Ensure adequate free disk space (>5GB)

### Error Logs
Error logs are saved to:
- **Windows:** `%APPDATA%\PowerHour\error.log`
- **macOS:** `~/Library/Application Support/PowerHour/error.log`
- **Linux:** `~/.config/PowerHour/error.log`

Access logs via Help → View Error Log

## Keyboard Shortcuts
- `Ctrl+O` - Browse for video source
- `Ctrl+S` - Save output as
- `Ctrl+R` - Start processing
- `Ctrl+C` - Cancel processing
- `Ctrl+L` - Clear log
- `Ctrl+Q` - Quit application
- `F1` - Show help
- `F11` - Toggle expert mode

## Performance Tips

1. **Video Quality Settings:**
   - Low: Fast processing, smaller file size
   - Medium: Balanced (recommended)
   - High: Best quality, slower processing

2. **Optimization:**
   - Process videos from local storage (not network drives)
   - Use SSD for temporary files
   - Keep videos under 1080p for faster processing

3. **Resource Usage:**
   - Processing uses ~2-4 GB RAM
   - CPU usage varies (50-100%)
   - Disk I/O intensive during concatenation

## Support

### Getting Help
- View built-in User Guide: Help → User Guide
- Check error logs for detailed information
- Review console output for FFmpeg messages

### Reporting Issues
When reporting issues, please include:
1. Operating system and version
2. Python version (`python --version`)
3. FFmpeg version (`ffmpeg -version`)
4. Error messages from logs
5. Steps to reproduce the issue

## License
This project is licensed under the MIT License. See LICENSE file for details.

## Credits
- Developed by Anthony Izzo
- Built with Python and Tkinter
- Video processing powered by FFmpeg
- Online video support via yt-dlp

---

**Version:** 1.0.0  
**Last Updated:** 2024