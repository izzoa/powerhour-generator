# PowerHour Video Generator - System Architecture

## Architecture Overview

The PowerHour Video Generator is built with a modular, thread-safe architecture that separates concerns between GUI presentation, video processing, and system integration.

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                      (powerhour_gui.py)                     │
├─────────────────────────────────────────────────────────────┤
│                      Threading Layer                         │
│                   (Queue-based messaging)                    │
├─────────────────────────────────────────────────────────────┤
│                     Processing Engine                        │
│                  (powerhour_processor.py)                   │
├─────────────────────────────────────────────────────────────┤
│                    External Dependencies                     │
│                 (FFmpeg, yt-dlp, psutil)                    │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. GUI Layer (powerhour_gui.py)

The presentation layer built with Tkinter that handles all user interactions.

#### Key Classes

```python
PowerHourGUI(tk.Tk)
├── UI Construction
│   ├── build_input_section()
│   ├── build_control_section()
│   ├── build_progress_section()
│   ├── build_log_section()
│   ├── build_menu_bar()
│   └── build_status_bar()
├── Validation
│   ├── validate_video_source()
│   ├── validate_common_clip()
│   ├── validate_fade_duration()
│   └── validate_output_file()
├── Configuration
│   ├── load_config()
│   ├── save_config()
│   └── add_to_recent()
└── Threading Control
    ├── start_processing()
    ├── cancel_processing()
    └── process_queue()
```

#### Responsibilities
- User interface rendering
- Input validation
- Configuration management
- Thread lifecycle management
- Message queue processing
- Error presentation

### 2. Processing Layer (powerhour_processor.py)

The business logic layer that handles actual video processing.

#### Key Classes

```python
ProcessorThread(threading.Thread)
├── Validation
│   ├── _validate_inputs()
│   └── _check_dependencies()
├── Processing Pipeline
│   ├── _process_videos()
│   ├── _download_playlist()
│   ├── _get_video_files()
│   └── _process_video_files()
├── Video Operations
│   ├── _get_video_duration()
│   ├── _analyze_loudness()
│   └── _reencode_video()
└── Communication
    ├── send_progress()
    ├── send_status()
    ├── send_log()
    └── send_error()
```

#### Responsibilities
- Video file processing
- FFmpeg integration
- Audio normalization
- Progress reporting
- Error handling
- Resource management

### 3. Communication Layer

Thread-safe message passing using Python's Queue.

#### Message Protocol

```python
# Message Types
{
    'type': 'progress',
    'current': int,
    'total': int
}

{
    'type': 'status',
    'message': str
}

{
    'type': 'log',
    'level': str,  # 'info', 'warning', 'error'
    'message': str
}

{
    'type': 'video_progress',
    'percent': float
}

{
    'type': 'complete',
    'output_file': str
}

{
    'type': 'error',
    'message': str
}
```

## Data Flow

### 1. Configuration Flow

```
Application Start
       │
       v
Load config.json ──> Apply Settings ──> UI Ready
       │                                     │
       └─────────────────────────────────────┘
                    (On Exit: Save)
```

### 2. Processing Flow

```
User Input ──> Validation ──> Create Thread ──> Process Videos
                                   │                  │
                                   v                  v
                            Message Queue <──── Status Updates
                                   │
                                   v
                            Update GUI ──> User Feedback
```

### 3. Video Processing Pipeline

```
Input Videos
     │
     v
┌─────────────────┐
│ Download (if URL)│
└─────────────────┘
     │
     v
┌─────────────────┐
│ Scan & Filter   │ (>80 seconds)
└─────────────────┘
     │
     v
┌─────────────────┐
│ Analyze Loudness│ (FFmpeg loudnorm)
└─────────────────┘
     │
     v
┌─────────────────┐
│ Re-encode Clips │ (60-second segments)
└─────────────────┘
     │
     v
┌─────────────────┐
│ Add Transitions │ (Common clips)
└─────────────────┘
     │
     v
┌─────────────────┐
│ Concatenate     │ (Final video)
└─────────────────┘
     │
     v
Output Video
```

## Threading Architecture

### Thread Safety

The application uses a producer-consumer pattern with thread-safe queues:

```python
Main Thread (GUI)              Worker Thread (Processing)
     │                                  │
     ├──> Start Processing ────────────>│
     │                                  │
     │<─── Queue Messages <─────────────┤
     │                                  │
     ├──> Process Messages              │
     │    Update UI                     │
     │                                  │
     ├──> Cancel Request ──────────────>│
     │                                  │
     │<─── Cleanup Complete <───────────┤
```

### Synchronization Points

1. **Thread Start**: GUI creates and starts ProcessorThread
2. **Message Queue**: All communication via thread-safe queue
3. **Cancellation**: Stop event for clean shutdown
4. **Completion**: Thread signals completion through queue

## Configuration Management

### Configuration Schema

```json
{
    "window_geometry": "800x600+100+100",
    "recent_sources": ["path1", "path2"],
    "recent_common_clips": ["clip1.mp4"],
    "recent_outputs": ["output1.mp4"],
    "default_fade_duration": 3.0,
    "last_video_source": "/path/to/videos",
    "last_common_clip": "/path/to/clip.mp4",
    "last_output_dir": "/path/to/output",
    "max_recent_items": 10,
    "video_quality": "medium",
    "audio_normalization": true,
    "output_format": "mp4",
    "expert_mode": false,
    "presets": {
        "custom_preset": {
            "fade_duration": 2.0,
            "video_quality": "high"
        }
    }
}
```

### Storage Locations

- **Windows**: `%APPDATA%\PowerHour\`
- **macOS**: `~/Library/Application Support/PowerHour/`
- **Linux**: `~/.config/PowerHour/`

## Error Handling Strategy

### Error Hierarchy

```
Exception
├── Input Validation Errors
│   ├── Missing files
│   ├── Invalid paths
│   └── Wrong formats
├── Processing Errors
│   ├── FFmpeg failures
│   ├── Download errors
│   └── Encoding issues
├── System Errors
│   ├── Disk space
│   ├── Permissions
│   └── Memory issues
└── Unexpected Errors
    └── Caught globally
```

### Error Flow

```
Error Occurs ──> Log to File ──> Map to User Message ──> Display Dialog
                      │                                         │
                      v                                         v
                 error.log                               Reset UI State
```

## External Dependencies

### Required Dependencies

#### FFmpeg
- **Purpose**: Video processing, encoding, effects
- **Integration**: Subprocess calls
- **Commands Used**:
  - `ffmpeg`: Encoding, effects, concatenation
  - `ffprobe`: Duration extraction, format detection

#### Python Standard Library
- `tkinter`: GUI framework
- `threading`: Concurrent processing
- `queue`: Thread communication
- `json`: Configuration storage
- `tempfile`: Temporary file management

### Optional Dependencies

#### yt-dlp
- **Purpose**: Download online videos
- **Integration**: Subprocess calls
- **Usage**: URL support for playlists

#### psutil
- **Purpose**: System resource monitoring
- **Integration**: Direct import
- **Usage**: CPU and memory display

## Performance Considerations

### Memory Management

```
Typical Memory Usage:
├── Application: 50-100 MB
├── Video buffers: 500-1000 MB
├── FFmpeg processes: 1-2 GB
└── Total: 2-4 GB
```

### Processing Optimization

1. **Random sampling**: Select 60 videos from larger collections
2. **Parallel analysis**: Loudness analysis before encoding
3. **Streaming encoding**: Process one video at a time
4. **Temp file cleanup**: Remove processed clips immediately

### I/O Optimization

- Use local temp directory for speed
- Process from SSD when possible
- Minimize file copies
- Stream processing where applicable

## Security Considerations

### Input Validation

All user inputs are validated:
- Path traversal prevention
- Command injection protection
- File type verification
- Size limitations

### Subprocess Security

```python
# Safe command construction
command = [
    'ffmpeg',
    '-i', validated_input_path,  # No shell interpretation
    '-o', validated_output_path
]
subprocess.run(command, shell=False)  # Never use shell=True
```

### File Operations

- Temporary files in system temp
- Automatic cleanup on exit
- Unique naming to prevent conflicts
- Permission checks before operations

## Extension Points

### Adding New Features

#### 1. New UI Section
```python
# In powerhour_gui.py
def build_new_section(self):
    """Add new UI section."""
    # Add to __init__ call
    # Implement builder method
    # Add configuration support
```

#### 2. New Processing Feature
```python
# In powerhour_processor.py
def _new_processing_step(self):
    """Add processing step."""
    # Add to pipeline
    # Send progress updates
    # Handle cancellation
```

#### 3. New Message Type
```python
# Define in both files
NEW_MESSAGE = {
    'type': 'new_type',
    'data': Any
}
# Add handler in process_queue()
```

## Testing Architecture

### Test Coverage Areas

```
Unit Tests
├── GUI Components
│   ├── Widget creation
│   ├── Event handlers
│   └── Validation logic
├── Processing Logic
│   ├── Video analysis
│   ├── FFmpeg commands
│   └── File operations
└── Integration
    ├── Thread communication
    ├── Configuration persistence
    └── Error handling
```

### Mock Strategy

```python
# Mock external dependencies
@patch('subprocess.run')
@patch('os.path.exists')
def test_processing(mock_exists, mock_run):
    mock_exists.return_value = True
    mock_run.return_value.returncode = 0
    # Test processing logic
```

## Deployment Considerations

### Packaging Structure

```
dist/
├── powerhour-gui.exe     # PyInstaller output
├── ffmpeg/               # Bundled FFmpeg
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── config/               # Default configs
└── docs/                 # User documentation
```

### Platform-Specific Builds

#### Windows
- PyInstaller with hidden imports
- Bundle FFmpeg binaries
- Create MSI installer

#### macOS
- py2app for .app bundle
- Code signing required
- DMG distribution

#### Linux
- AppImage for portability
- Snap/Flatpak packages
- Debian/RPM packages

## Future Architecture Improvements

### Planned Enhancements

1. **Plugin System**
   - Dynamic feature loading
   - Custom effects API
   - Third-party integrations

2. **Distributed Processing**
   - Split video processing
   - Cloud rendering support
   - Multi-machine coordination

3. **Web Interface**
   - REST API backend
   - WebSocket progress updates
   - Browser-based UI

4. **Database Backend**
   - SQLite for metadata
   - Processing history
   - Advanced preset management

---

*PowerHour Video Generator - Architecture Documentation*  
*Version 1.0.0*