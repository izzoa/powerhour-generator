# PowerHour Video Generator - User Guide

## Complete Guide to Creating PowerHour Videos

### Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Interface Overview](#main-interface-overview)
4. [Step-by-Step Tutorial](#step-by-step-tutorial)
5. [Advanced Features](#advanced-features)
6. [Menu Options](#menu-options)
7. [Presets and Configurations](#presets-and-configurations)
8. [Understanding Progress Indicators](#understanding-progress-indicators)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Tips and Best Practices](#tips-and-best-practices)
11. [FAQ](#frequently-asked-questions)

---

## Introduction

PowerHour Video Generator creates hour-long party videos by combining 60 one-minute clips with smooth transitions. Perfect for:
- Party games and drinking games
- Music video compilations
- Highlight reels
- Custom video mixes

### What is a PowerHour?
A PowerHour is traditionally a drinking game where participants take a shot of beer every minute for an hour. This tool creates the accompanying video that changes every minute, typically featuring music videos, movie clips, or custom content.

---

## Getting Started

### First Launch
When you first launch the application:

1. **Check Dependencies**: The app will verify FFmpeg is installed
2. **Load Configuration**: Previous settings are automatically restored
3. **Interface Ready**: All controls are enabled and ready to use

*[Screenshot: Main window on first launch]*

### Understanding the Layout

The interface is divided into five main sections:

1. **Input Parameters** (Top)
   - Video source selection
   - Common clip selection
   - Fade duration control
   - Output file specification

2. **Control Panel** (Middle)
   - Start Processing button
   - Cancel button
   - Status display

3. **Progress Tracking** (Center)
   - Current video progress
   - Overall progress
   - ETA and speed indicators

4. **Output Log** (Bottom)
   - Real-time processing messages
   - Error and warning display
   - Clear log button

5. **Menu Bar** (Top)
   - Options menu
   - Help menu

---

## Main Interface Overview

### Input Parameters Section

#### Video Source
- **Purpose**: Select the folder containing your video files or paste a playlist URL
- **Browse Button**: Opens folder selection dialog
- **Dropdown**: Shows recent sources for quick access
- **Validation**: Green border = valid, Red border = invalid

#### Common Clip
- **Purpose**: Select the transition video that plays between each main clip
- **Recommended**: 3-5 second clips work best
- **Browse Button**: Opens file selection dialog
- **Dropdown**: Recent clips for reuse

#### Fade Duration
- **Range**: 0-10 seconds
- **Default**: 3 seconds
- **Effect**: Controls how smoothly videos transition
- **Tip**: Higher values create smoother but longer transitions

#### Output File
- **Default**: powerhour_output.mp4
- **Save As Button**: Choose location and filename
- **Format**: MP4 recommended for compatibility

### Control Section

#### Start Processing Button (Green)
- **Function**: Begins video processing
- **State**: Disabled during processing
- **Validation**: Checks all inputs before starting

#### Cancel Button (Red)
- **Function**: Stops current processing
- **State**: Only enabled during processing
- **Confirmation**: Asks before cancelling

#### Status Display
Shows current operation:
- "Ready" - Waiting to start
- "Processing..." - Working on videos
- "Complete" - Finished successfully
- "Error" - Problem occurred

---

## Step-by-Step Tutorial

### Basic PowerHour Creation

#### Step 1: Prepare Your Videos
1. Collect at least 60 video files
2. Ensure each is at least 80 seconds long
3. Place them in a single folder

*[Screenshot: Folder with video files]*

#### Step 2: Launch the Application
```bash
python powerhour_gui.py
```

#### Step 3: Select Video Source
1. Click "Browse" next to Video Source
2. Navigate to your video folder
3. Select the folder and click "OK"
4. The path appears with a green validation border

*[Screenshot: Video source selection]*

#### Step 4: Choose Common Clip
1. Click "Browse" next to Common Clip
2. Select your transition video file
3. This clip plays between each main video

*[Screenshot: Common clip selection]*

#### Step 5: Configure Settings
1. Set Fade Duration (3 seconds recommended)
2. Choose output location with "Save As"
3. Verify all fields have green validation

*[Screenshot: Configured settings]*

#### Step 6: Start Processing
1. Click the green "Start Processing" button
2. Watch progress in real-time
3. Monitor the log for any issues
4. Processing takes 10-30 minutes typically

*[Screenshot: Processing in progress]*

#### Step 7: Completion
1. "Processing Complete" dialog appears
2. Your video is saved to the specified location
3. Recent items are saved for next time

*[Screenshot: Completion dialog]*

### Using Online Playlists

#### YouTube Playlist Download
1. Copy the playlist URL from YouTube
2. Paste directly into Video Source field
3. Ensure yt-dlp is installed
4. Processing will download then process videos

Example URL formats:
- `https://www.youtube.com/playlist?list=PLxxxxxx`
- `https://www.youtube.com/watch?v=xxxx&list=PLxxxx`

---

## Advanced Features

### Expert Mode

#### Enabling Expert Mode
1. Go to Options → Expert Mode
2. Additional controls appear in progress section
3. FFmpeg parameters become editable

#### FFmpeg Parameters
Default: `-c:v libx264 -preset medium -crf 23`

Modify for:
- **Faster encoding**: `-preset ultrafast`
- **Better quality**: `-crf 18`
- **Smaller files**: `-crf 28`

*[Screenshot: Expert mode panel]*

### Preset System

#### Built-in Presets

**Quick Party Mix**
- Medium quality
- Fast processing
- 2-second fades
- Optimized for parties

**High Quality Archive**
- Maximum quality
- Slower processing
- 3-second fades
- Best for permanent collections

**Fast Processing**
- Low quality
- Fastest encoding
- 1-second fades
- When time is critical

#### Custom Presets

##### Saving a Preset
1. Configure all settings as desired
2. Options → Presets → Save Current Settings
3. Enter a memorable name
4. Preset is saved for future use

##### Loading a Preset
1. Options → Presets → Load Preset
2. Select from your saved presets
3. All settings update immediately

---

## Menu Options

### Options Menu

#### Video Quality
- **Low**: Fast processing, smaller files (CRF 28)
- **Medium**: Balanced quality/speed (CRF 23)
- **High**: Best quality, larger files (CRF 18)

#### Audio Normalization
- **Enabled** (default): Consistent volume across clips
- **Disabled**: Original audio levels preserved

#### Output Format
- **MP4**: Best compatibility (recommended)
- **AVI**: Legacy format support
- **MKV**: Advanced features, larger files

### Help Menu

#### About PowerHour
Shows version and copyright information

#### User Guide
Opens this comprehensive guide

#### Keyboard Shortcuts
Quick reference for all shortcuts

#### View Error Log
Opens error log in system text editor

#### Check for Updates
Verifies you have the latest version

---

## Presets and Configurations

### Configuration Persistence

The following settings are saved automatically:
- Window size and position
- Last used video source
- Last used common clip
- Fade duration preference
- Output directory
- Quality settings
- Recent items lists (last 10)

### Configuration File Locations

#### Windows
`%APPDATA%\PowerHour\config.json`

#### macOS
`~/Library/Application Support/PowerHour/config.json`

#### Linux
`~/.config/PowerHour/config.json`

### Manual Configuration Editing

Example config.json:
```json
{
    "window_geometry": "800x600",
    "last_video_source": "/Users/videos/",
    "last_common_clip": "/Users/transition.mp4",
    "default_fade_duration": 3.0,
    "video_quality": "medium",
    "audio_normalization": true,
    "recent_sources": [
        "/Users/videos/",
        "/Users/music_videos/"
    ]
}
```

---

## Understanding Progress Indicators

### Current Video Progress
- Shows encoding progress for individual clips
- Resets for each video
- 0-100% scale

### Overall Progress
- Tracks total videos processed
- Shows "X/60 videos"
- Main indicator of completion

### ETA (Estimated Time Remaining)
- Calculated from average processing speed
- Updates after each video
- Format: "~X minutes Y seconds remaining"

### Processing Speed
- Shows videos per minute
- Rolling average of last 10 videos
- Helps estimate total time

### Processing Stages

1. **Initializing**: Setting up processing
2. **Downloading**: Getting online videos (if URL)
3. **Analyzing**: Checking video durations and loudness
4. **Encoding**: Processing individual clips
5. **Finalizing**: Creating final video

### Status Bar Information

#### Left: Hints
- Context-sensitive tips
- Current mode indicators

#### Center: Current Operation
- Detailed processing status
- File being processed

#### Right: Resource Usage
- CPU percentage
- RAM usage
- Updates every 2 seconds

---

## Troubleshooting Guide

### Common Problems and Solutions

#### Problem: "FFmpeg not found"
**Solution:**
1. Verify FFmpeg installation: `ffmpeg -version`
2. Add FFmpeg to system PATH
3. Restart the application

#### Problem: "No valid videos found"
**Causes:**
- Videos shorter than 80 seconds
- Unsupported formats
- Empty folder

**Solution:**
- Use longer videos (80+ seconds)
- Convert to supported formats (MP4, AVI, MKV)
- Check folder contains video files

#### Problem: Processing is very slow
**Solutions:**
1. Use Low Quality preset
2. Close other applications
3. Process fewer videos at once
4. Check available disk space (need 5+ GB)

#### Problem: "Permission denied" errors
**Windows:**
- Run as Administrator
- Check antivirus settings

**macOS/Linux:**
- Check folder permissions: `ls -la`
- Use chmod if needed: `chmod 755 folder`

#### Problem: Application won't start
**Check:**
1. Python version: `python --version` (need 3.8+)
2. Tkinter installed: `python -m tkinter`
3. No syntax errors: Check console output

#### Problem: Output video has no sound
**Possible causes:**
- Source videos have no audio
- Audio codec issues

**Solution:**
- Verify source videos have audio
- Enable audio normalization
- Try different output format

### Reading Error Logs

#### Log Levels
- **Info (Black)**: Normal operations
- **Warning (Orange)**: Non-critical issues
- **Error (Red)**: Problems requiring attention

#### Finding Detailed Logs
1. Help → View Error Log
2. Look for timestamps
3. Search for "ERROR" or "FAILED"
4. Note FFmpeg command output

### Getting Help

#### Information to Provide
1. Operating system and version
2. Python version
3. FFmpeg version
4. Complete error message
5. Steps to reproduce
6. Screenshots if applicable

---

## Tips and Best Practices

### Video Selection
1. **Quality**: Use similar quality videos for consistency
2. **Content**: Mix genres for variety
3. **Duration**: Longer videos give more random selection
4. **Format**: Stick to common formats (MP4)

### Performance Optimization
1. **Local Storage**: Process from local drives, not network
2. **SSD Preferred**: Faster read/write speeds
3. **Close Programs**: Free up CPU and RAM
4. **Batch Size**: Process 60-80 videos maximum

### Quality vs Speed Trade-offs

| Setting | Quality | Speed | File Size |
|---------|---------|-------|-----------|
| Low | ★★☆☆☆ | ★★★★★ | Small |
| Medium | ★★★★☆ | ★★★☆☆ | Medium |
| High | ★★★★★ | ★☆☆☆☆ | Large |

### Common Clip Best Practices
1. **Duration**: 3-5 seconds optimal
2. **Content**: Logo, countdown, or transition effect
3. **Audio**: Include audio cue for timing
4. **Resolution**: Match your target output (720p)

### Output Recommendations
1. **Filename**: Include date for organization
2. **Location**: Save to drive with space
3. **Backup**: Keep source videos after processing
4. **Format**: MP4 for maximum compatibility

---

## Frequently Asked Questions

### General Questions

**Q: How long does processing take?**
A: Typically 10-30 minutes for 60 videos, depending on:
- Computer speed
- Quality settings
- Video resolutions
- Disk speed

**Q: Can I use videos shorter than 60 seconds?**
A: Yes, but they must be at least 80 seconds to allow for random start points and 60-second extraction.

**Q: What video formats are supported?**
A: Any format FFmpeg supports: MP4, AVI, MKV, MOV, WMV, FLV, and more.

**Q: Can I pause and resume processing?**
A: Not currently. Processing must complete or be cancelled entirely.

### Technical Questions

**Q: Why does it need 80-second videos for 60-second clips?**
A: The extra 20 seconds allows random start points (10-70 seconds) for variety.

**Q: How does audio normalization work?**
A: Uses FFmpeg's loudnorm filter to analyze and adjust audio to -23 LUFS standard.

**Q: Can I change the output resolution?**
A: Currently fixed at 1280x720. Modify source code for other resolutions.

**Q: Is GPU acceleration supported?**
A: Not by default. Expert users can modify FFmpeg parameters for hardware encoding.

### Troubleshooting Questions

**Q: Why does my output have black bars?**
A: Videos are scaled to 1280x720. Different aspect ratios get letterboxing.

**Q: Can I process videos from network drives?**
A: Yes, but it's much slower. Copy locally for best performance.

**Q: Why do some videos fail to process?**
A: Usually codec issues. Check log for specific FFmpeg errors.

**Q: How do I process more than 60 videos?**
A: The app randomly selects 60 from your folder if more are present.

---

## Appendix

### Keyboard Shortcuts Reference
| Shortcut | Action |
|----------|--------|
| Ctrl+O | Browse video source |
| Ctrl+S | Save output as |
| Ctrl+R | Start processing |
| Ctrl+C | Cancel processing |
| Ctrl+L | Clear log |
| Ctrl+Q | Quit |
| F1 | Show help |
| F5 | Refresh validation |
| F11 | Toggle expert mode |

### File Structure
```
powerhour-generator/
├── powerhour_gui.py        # Main GUI application
├── powerhour_processor.py  # Processing thread
├── README_GUI.md           # Quick start guide
├── USER_GUIDE.md          # This comprehensive guide
└── config/                # Configuration storage
```

### Support Resources
- Error log location varies by OS (see Configuration section)
- FFmpeg documentation: https://ffmpeg.org/documentation.html
- Python Tkinter guide: https://docs.python.org/3/library/tkinter.html

---

*PowerHour Video Generator v1.0.0 - User Guide*  
*Last updated: 2024*