"""
PowerHour Video Generator GUI

A comprehensive Tkinter-based graphical interface for the PowerHour video generator.
This module provides an intuitive GUI for creating PowerHour videos - hour-long
compilations of 60 one-minute video clips with customizable transitions.

Key Features:
    - Video source selection (local folders or URLs)
    - Common clip transitions between videos
    - Configurable fade duration (0-10 seconds)
    - Real-time progress tracking with ETA
    - Threaded processing for non-blocking UI
    - Configuration persistence across sessions
    - Error handling with detailed logging
    - Expert mode for advanced users
    - Preset system for quick configuration

Classes:
    PowerHourGUI: Main application window extending tk.Tk

Dependencies:
    - tkinter: GUI framework
    - powerhour_processor: Backend video processing
    - psutil (optional): System resource monitoring
    - ffmpeg: External video processing tool

Author: Anthony Izzo
Version: 1.0.0
License: MIT
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import queue
import json
import os
from pathlib import Path
import sys
import time
import re
import platform
import traceback
import tempfile
import atexit
from datetime import datetime
from typing import Optional, Dict, Any

# Import the processor for video generation
try:
    from .powerhour_processor import ProcessorThread
except ImportError:
    try:
        # Fallback for when running as a script
        from powerhour_processor import ProcessorThread
    except ImportError as e:
        print(f"Error: Could not import ProcessorThread: {e}")
        print("Please ensure powerhour_processor.py is in the same directory.")
        sys.exit(1)

# Try to import psutil for resource monitoring (optional)
try:
    import psutil
except ImportError:
    psutil = None


class PowerHourGUI(tk.Tk):
    """
    Main GUI application class for PowerHour Video Generator.
    
    This class creates and manages the entire GUI application for generating
    PowerHour videos. It handles user input, video processing coordination,
    progress tracking, and configuration management.
    
    Attributes:
        config (Dict[str, Any]): Application configuration settings
        config_file (str): Path to the configuration JSON file
        processing_thread (Optional[ProcessorThread]): Active video processing thread
        message_queue (queue.Queue): Queue for thread communication
        temp_files (List[str]): List of temporary files for cleanup
        error_log_file (str): Path to the error log file
        
    Methods:
        build_*: Methods to construct UI sections
        validate_*: Input validation methods
        browse_*: File/folder selection methods
        *_processing: Video processing control methods
        
    Complexity: O(1) for UI operations, O(n) for processing n videos
    """
    
    def __init__(self) -> None:
        """
        Initialize the PowerHour GUI application.
        
        Sets up the main window, loads configuration, creates all UI components,
        and establishes event handlers. Configures exception handling and cleanup
        procedures for robust operation.
        
        Raises:
            SystemExit: If required dependencies are not available
            
        Complexity: O(1) - UI construction is constant time
        Flow: Called once at application startup
        """
        super().__init__()
        
        # Set up global exception handler
        self.setup_exception_handler()
        
        # Initialize error log
        self.error_log_file = self.get_error_log_path()
        
        # Track temporary files for cleanup
        self.temp_files = []
        
        # Register cleanup on exit
        atexit.register(self.cleanup_on_exit)
        
        # Initialize configuration
        self.app_config = self.get_default_config()
        self.config_file = self.get_config_path()
        self.load_config()
        
        # Set window properties
        self.title("PowerHour Video Generator")
        
        # Apply saved geometry or default
        if 'window_geometry' in self.app_config:
            self.geometry(self.app_config['window_geometry'])
        else:
            self.geometry("800x600")
        self.minsize(600, 400)
        
        # Configure grid weights for responsive layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=2)
        self.grid_columnconfigure(0, weight=1)
        
        # Initialize processing state
        self.processing_start_time = None
        self.videos_processed = 0
        self.processing_speed = []
        self.current_file_being_processed = ""
        self.processing_stage = ""
        
        # Initialize instance variables for widgets
        self.video_source_var = tk.StringVar(value=self.app_config.get('last_video_source', ''))
        self.common_clip_var = tk.StringVar(value=self.app_config.get('last_common_clip', ''))
        self.fade_duration_var = tk.DoubleVar(value=self.app_config.get('default_fade_duration', 3.0))
        
        # Set output file with default directory
        last_output_dir = self.app_config.get('last_output_dir', '')
        if last_output_dir:
            default_output = os.path.join(last_output_dir, "powerhour_output.mp4")
        else:
            default_output = "powerhour_output.mp4"
        self.output_file_var = tk.StringVar(value=default_output)
        self.status_var = tk.StringVar(value="Ready")
        self.current_progress_var = tk.DoubleVar()
        self.overall_progress_var = tk.IntVar()
        self.eta_var = tk.StringVar(value="")
        
        # Initialize queue for thread communication
        self.message_queue = queue.Queue()
        self.processing_thread = None
        
        # Build GUI sections
        self.build_menu_bar()
        self.build_input_section()
        self.build_control_section()
        self.build_progress_section()
        self.build_log_section()
        self.build_status_bar()
        
        # Bind window close event to save config
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start queue processing
        self.process_queue()
        
        # Log startup
        self.log_to_file("info", "Application started")
    
    def build_input_section(self) -> None:
        """
        Create the input parameters section of the GUI.
        
        Builds the input form with video source selection, common clip selection,
        fade duration control, and output file specification. Includes validation
        and recent items dropdowns for improved user experience.
        
        Returns:
            None
            
        Complexity: O(1) - UI construction is constant time
        Flow: Called once during initialization by __init__
        Dependencies: Requires self.app_config to be loaded first
        """
        # Create LabelFrame for input parameters
        input_frame = ttk.LabelFrame(self, text="Input Parameters", padding=10)
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Configure grid weights for responsive layout
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Video Source Input with Recent Items
        ttk.Label(input_frame, text="Video Source (Folder/URL):").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        
        # Create frame for entry and dropdown
        video_source_frame = ttk.Frame(input_frame)
        video_source_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        video_source_frame.grid_columnconfigure(0, weight=1)
        
        # Recent sources dropdown
        self.video_source_combo = ttk.Combobox(
            video_source_frame,
            textvariable=self.video_source_var,
            values=self.app_config.get('recent_sources', [])
        )
        self.video_source_combo.grid(row=0, column=0, sticky="ew")
        self.video_source_combo.bind("<FocusOut>", self.validate_video_source)
        self.video_source_combo.bind("<KeyRelease>", self.validate_video_source_realtime)
        self.video_source_combo.bind("<<ComboboxSelected>>", self.validate_video_source)
        
        ttk.Button(
            input_frame, text="Browse", command=self.browse_video_source
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Common Clip Input with Recent Items
        ttk.Label(input_frame, text="Common Clip:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        
        # Create frame for entry and dropdown
        common_clip_frame = ttk.Frame(input_frame)
        common_clip_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        common_clip_frame.grid_columnconfigure(0, weight=1)
        
        # Recent clips dropdown
        self.common_clip_combo = ttk.Combobox(
            common_clip_frame,
            textvariable=self.common_clip_var,
            values=self.app_config.get('recent_common_clips', [])
        )
        self.common_clip_combo.grid(row=0, column=0, sticky="ew")
        self.common_clip_combo.bind("<FocusOut>", self.validate_common_clip)
        self.common_clip_combo.bind("<KeyRelease>", self.validate_common_clip_realtime)
        self.common_clip_combo.bind("<<ComboboxSelected>>", self.validate_common_clip)
        
        ttk.Button(
            input_frame, text="Browse", command=self.browse_common_clip
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # Fade Duration Input with tooltip
        fade_label = ttk.Label(input_frame, text="Fade Duration (seconds):")
        fade_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.add_tooltip(fade_label,
                        "Duration of fade in/out effect between video clips (0-10 seconds)")
        
        self.fade_duration_spinbox = ttk.Spinbox(
            input_frame,
            from_=0,
            to=10,
            increment=0.5,
            textvariable=self.fade_duration_var,
            width=10
        )
        self.fade_duration_spinbox.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.fade_duration_spinbox.bind("<KeyRelease>", self.validate_fade_duration)
        self.fade_duration_spinbox.bind("<FocusOut>", self.validate_fade_duration)
        ttk.Label(input_frame, text="Transition effect duration").grid(
            row=2, column=2, sticky="w", padx=5, pady=5)
        
        # Output File Input with Recent Directories
        ttk.Label(input_frame, text="Output File:").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        
        # Create frame for entry and dropdown
        output_frame = ttk.Frame(input_frame)
        output_frame.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        output_frame.grid_columnconfigure(0, weight=1)
        
        # Recent outputs dropdown
        self.output_file_combo = ttk.Combobox(
            output_frame,
            textvariable=self.output_file_var,
            values=self.app_config.get('recent_outputs', [])
        )
        self.output_file_combo.grid(row=0, column=0, sticky="ew")
        self.output_file_combo.bind("<KeyRelease>", self.validate_output_file_realtime)
        self.output_file_combo.bind("<FocusOut>", self.validate_output_file)
        self.output_file_combo.bind("<<ComboboxSelected>>", self.validate_output_file)
        
        ttk.Button(
            input_frame, text="Save As", command=self.browse_output_file
        ).grid(row=3, column=2, padx=5, pady=5)
    
    def build_control_section(self) -> None:
        """
        Create the control section with Start/Cancel buttons and status display.
        
        Builds the main control interface with processing controls and real-time
        status updates. Buttons are color-coded for visual clarity (green for start,
        red for cancel).
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called once during initialization by __init__
        """
        # Create Frame for controls
        control_frame = ttk.Frame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Configure grid for centered layout
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=0)
        control_frame.grid_columnconfigure(2, weight=0)
        control_frame.grid_columnconfigure(3, weight=1)
        control_frame.grid_columnconfigure(4, weight=2)
        
        # Start button (using ttk for better cross-platform compatibility)
        self.start_button = ttk.Button(
            control_frame,
            text="Start Processing",
            command=self.start_processing,
            width=15,
            style="Start.TButton"
        )
        self.start_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Cancel button (initially disabled)
        self.cancel_button = ttk.Button(
            control_frame,
            text="Cancel",
            command=self.cancel_processing,
            width=15,
            state="disabled",
            style="Cancel.TButton"
        )
        self.cancel_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Status label
        self.status_label = ttk.Label(
            control_frame,
            textvariable=self.status_var,
            font=("Arial", 10)
        )
        self.status_label.grid(row=0, column=4, sticky="w", padx=20, pady=5)
    
    def build_menu_bar(self) -> None:
        """
        Create the application menu bar with Options and Help menus.
        
        Builds a comprehensive menu system including:
        - Video quality settings (low/medium/high)
        - Output format options (MP4/AVI/MKV)
        - Audio normalization toggle
        - Expert mode for advanced users
        - Preset management system
        - Help and documentation access
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called once during initialization by __init__
        Dependencies: Requires self.app_config for initial values
        """
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        
        # Video quality submenu
        quality_menu = tk.Menu(options_menu, tearoff=0)
        self.video_quality_var = tk.StringVar(value=self.app_config.get('video_quality', 'medium'))
        quality_menu.add_radiobutton(label="Low Quality (Fast)",
                                    variable=self.video_quality_var,
                                    value="low")
        quality_menu.add_radiobutton(label="Medium Quality (Balanced)",
                                    variable=self.video_quality_var,
                                    value="medium")
        quality_menu.add_radiobutton(label="High Quality (Slow)",
                                    variable=self.video_quality_var,
                                    value="high")
        options_menu.add_cascade(label="Video Quality", menu=quality_menu)
        
        # Audio normalization option
        self.audio_normalization_var = tk.BooleanVar(
            value=self.app_config.get('audio_normalization', True)
        )
        options_menu.add_checkbutton(label="Audio Normalization",
                                    variable=self.audio_normalization_var)
        
        # Output format submenu
        format_menu = tk.Menu(options_menu, tearoff=0)
        self.output_format_var = tk.StringVar(value=self.app_config.get('output_format', 'mp4'))
        format_menu.add_radiobutton(label="MP4",
                                   variable=self.output_format_var,
                                   value="mp4")
        format_menu.add_radiobutton(label="AVI",
                                   variable=self.output_format_var,
                                   value="avi")
        format_menu.add_radiobutton(label="MKV",
                                   variable=self.output_format_var,
                                   value="mkv")
        options_menu.add_cascade(label="Output Format", menu=format_menu)
        
        options_menu.add_separator()
        
        # Expert mode
        self.expert_mode_var = tk.BooleanVar(value=self.app_config.get('expert_mode', False))
        options_menu.add_checkbutton(label="Expert Mode",
                                    variable=self.expert_mode_var,
                                    command=self.toggle_expert_mode)
        
        # Presets menu
        options_menu.add_separator()
        presets_menu = tk.Menu(options_menu, tearoff=0)
        presets_menu.add_command(label="Save Current Settings as Preset",
                               command=self.save_preset)
        presets_menu.add_command(label="Load Preset",
                               command=self.load_preset)
        presets_menu.add_separator()
        presets_menu.add_command(label="Quick Party Mix",
                               command=lambda: self.apply_preset('party'))
        presets_menu.add_command(label="High Quality Archive",
                               command=lambda: self.apply_preset('archive'))
        presets_menu.add_command(label="Fast Processing",
                               command=lambda: self.apply_preset('fast'))
        options_menu.add_cascade(label="Presets", menu=presets_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="About PowerHour", command=self.show_about)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="View Error Log", command=self.view_error_log)
        help_menu.add_command(label="Check for Updates", command=self.check_updates)
    
    def build_status_bar(self) -> None:
        """
        Create the status bar at bottom of window.
        
        Creates a multi-part status bar displaying:
        - Contextual hints (left side)
        - Current operation details (center)
        - System resource usage (right side)
        
        Starts automatic resource monitoring that updates every 2 seconds.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called once during initialization, updates every 2 seconds
        """
        self.status_bar = ttk.Frame(self)
        self.status_bar.grid(row=4, column=0, sticky="ew", padx=5, pady=2)
        
        # Left side - hints
        self.hint_label = ttk.Label(self.status_bar, text="Ready to create PowerHour videos",
                                   font=("Arial", 9))
        self.hint_label.pack(side="left", padx=5)
        
        # Right side - resource usage
        self.resource_label = ttk.Label(self.status_bar, text="", font=("Arial", 9))
        self.resource_label.pack(side="right", padx=5)
        
        # Center - current operation
        self.operation_label = ttk.Label(self.status_bar, text="", font=("Arial", 9, "italic"))
        self.operation_label.pack(side="left", padx=20)
        
        # Start resource monitoring
        self.update_resource_usage()
    
    def build_progress_section(self) -> None:
        """
        Create the progress tracking section with multiple indicators.
        
        Builds comprehensive progress display including:
        - Current video progress bar (0-100%)
        - Overall progress bar (0-60 videos)
        - ETA calculation and display
        - Current file being processed
        - Processing stage indicator
        - Speed indicator (videos/minute)
        - Expert mode section (hidden by default)
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called once during initialization by __init__
        """
        # Create LabelFrame for progress
        progress_frame = ttk.LabelFrame(self, text="Processing Progress", padding=10)
        progress_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Configure grid weights
        progress_frame.grid_columnconfigure(1, weight=1)
        
        # Current video progress
        ttk.Label(progress_frame, text="Current Video:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.current_progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.current_progress_var,
            maximum=100,
            mode='determinate'
        )
        self.current_progress_bar.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.current_progress_label = ttk.Label(progress_frame, text="0%")
        self.current_progress_label.grid(row=0, column=2, padx=5, pady=5)
        
        # Overall progress
        ttk.Label(progress_frame, text="Overall Progress:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.overall_progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.overall_progress_var,
            maximum=60,
            mode='determinate'
        )
        self.overall_progress_bar.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.overall_progress_label = ttk.Label(progress_frame, text="0/60 videos")
        self.overall_progress_label.grid(row=1, column=2, padx=5, pady=5)
        
        # ETA and speed display
        ttk.Label(progress_frame, text="Estimated Time Remaining:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.eta_label = ttk.Label(
            progress_frame,
            textvariable=self.eta_var,
            font=("Arial", 10, "italic")
        )
        self.eta_label.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Processing details (Phase 6)
        ttk.Label(progress_frame, text="Current File:").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        self.current_file_label = ttk.Label(progress_frame, text="",
                                           font=("Arial", 9))
        self.current_file_label.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(progress_frame, text="Processing Stage:").grid(
            row=4, column=0, sticky="w", padx=5, pady=5
        )
        self.processing_stage_label = ttk.Label(progress_frame, text="",
                                               font=("Arial", 9, "bold"))
        self.processing_stage_label.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(progress_frame, text="Speed:").grid(
            row=5, column=0, sticky="w", padx=5, pady=5
        )
        self.speed_label = ttk.Label(progress_frame, text="",
                                    font=("Arial", 9))
        self.speed_label.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        # Expert mode section (initially hidden)
        self.expert_frame = ttk.LabelFrame(progress_frame, text="Expert Details",
                                         padding=5)
        # Don't grid it initially - will be shown in expert mode
        
        self.ffmpeg_params_label = ttk.Label(self.expert_frame,
                                            text="FFmpeg Parameters:",
                                            font=("Arial", 9))
        self.ffmpeg_params_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.ffmpeg_params_text = tk.Text(self.expert_frame, height=3, width=60,
                                         font=("Courier", 8))
        self.ffmpeg_params_text.grid(row=1, column=0, padx=5, pady=2)
        self.ffmpeg_params_text.insert("1.0", "-c:v libx264 -preset medium -crf 23")
    
    def build_log_section(self) -> None:
        """
        Create the output log section for displaying messages.
        
        Creates a scrollable text area with color-coded messages:
        - Info messages in black
        - Warning messages in orange
        - Error messages in red
        
        Includes auto-scroll functionality and a clear button.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called once during initialization by __init__
        """
        # Create LabelFrame for log
        log_frame = ttk.LabelFrame(self, text="Output Log", padding=10)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        
        # Configure grid weights
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # Create frame for log and buttons
        log_container = ttk.Frame(log_frame)
        log_container.grid(row=0, column=0, sticky="nsew")
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)
        
        # ScrolledText widget for log output
        self.log_text = ScrolledText(
            log_container,
            height=10,
            wrap=tk.WORD,
            font=("Courier", 9),
            state="disabled"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure tags for colored text
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
        
        # Clear log button
        button_frame = ttk.Frame(log_frame)
        button_frame.grid(row=1, column=0, sticky="e", pady=5)
        ttk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_log
        ).pack(side="right")
    
    def log_info(self, message: str) -> None:
        """
        Log an informational message with black text.
        
        Args:
            message: The message to display in the log
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called throughout application for status updates
        """
        self.log_message(message, "info")
    
    def log_warning(self, message: str) -> None:
        """
        Log a warning message with orange text.
        
        Args:
            message: The warning message to display
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when non-critical issues occur
        """
        self.log_message(message, "warning")
    
    def log_error(self, message: str) -> None:
        """
        Log an error message with red text.
        
        Args:
            message: The error message to display
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when errors occur during processing
        """
        self.log_message(message, "error")
    
    def log_message(self, message: str, tag: str = "info") -> None:
        """
        Generic log message method with auto-scroll functionality.
        
        Adds a message to the log display with appropriate color tagging
        and automatically scrolls to show the latest message.
        
        Args:
            message: The message to log
            tag: Color tag - "info" (black), "warning" (orange), or "error" (red)
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called by specific log methods (log_info, log_warning, log_error)
        """
        # Check if log_text widget has been created yet
        if hasattr(self, 'log_text'):
            self.log_text.config(state="normal")
            self.log_text.insert("end", f"{message}\n", tag)
            self.log_text.see("end")  # Auto-scroll to bottom
            self.log_text.config(state="disabled")
    
    def clear_log(self) -> None:
        """
        Clear all messages from the log output.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when user clicks Clear Log button
        """
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
    
    def browse_video_source(self) -> None:
        """
        Open file dialog to browse for video source folder.
        
        Opens a directory selection dialog and updates the video source
        input with the selected path. Validates the selection immediately
        after selection.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when user clicks Browse button for video source
        """
        try:
            folder = filedialog.askdirectory(
                title="Select Video Source Folder",
                initialdir=os.getcwd()
            )
            if folder:
                self.video_source_var.set(folder)
                self.validate_video_source()
        except Exception as e:
            self.handle_error(e, "Failed to browse for video source")
    
    def browse_common_clip(self) -> None:
        """
        Open file dialog to browse for common clip video file.
        
        Opens a file selection dialog filtered for video files (mp4, avi, mkv, mov)
        and updates the common clip input with the selected file path.
        Validates the selection immediately.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when user clicks Browse button for common clip
        """
        try:
            filename = filedialog.askopenfilename(
                title="Select Common Clip",
                filetypes=[
                    ("Video files", "*.mp4 *.avi *.mkv *.mov"),
                    ("All files", "*.*")
                ],
                initialdir=os.getcwd()
            )
            if filename:
                self.common_clip_var.set(filename)
                self.validate_common_clip()
        except Exception as e:
            self.handle_error(e, "Failed to browse for common clip")
    
    def browse_output_file(self) -> None:
        """
        Open file dialog to browse for output file save location.
        
        Opens a save file dialog with .mp4 as default extension and updates
        the output file input with the selected path.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when user clicks Save As button for output file
        """
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Output File As",
                defaultextension=".mp4",
                filetypes=[
                    ("MP4 files", "*.mp4"),
                    ("All files", "*.*")
                ],
                initialdir=os.getcwd(),
                initialfile=self.output_file_var.get()
            )
            if filename:
                self.output_file_var.set(filename)
        except Exception as e:
            self.handle_error(e, "Failed to browse for output file")
    
    def validate_video_source(self, event: Optional[tk.Event] = None) -> bool:
        """
        Validate that the video source path exists and is accessible.
        
        Checks if the source is a valid URL or an existing directory.
        Updates the visual style of the input field based on validation result.
        
        Args:
            event: Optional Tkinter event (for event binding)
            
        Returns:
            bool: True if valid, False otherwise
            
        Complexity: O(1)
        Flow: Called on focus out, selection, or manual validation
        """
        path = self.video_source_var.get()
        if path:
            # Check if it's a URL or a folder
            if path.startswith("http"):
                # URL validation (basic check)
                self.video_source_combo.configure(style="Valid.TCombobox")
                return True
            elif os.path.isdir(path):
                self.video_source_combo.configure(style="Valid.TCombobox")
                return True
            else:
                self.video_source_combo.configure(style="Invalid.TCombobox")
                return False
        return False
    
    def validate_common_clip(self, event: Optional[tk.Event] = None) -> bool:
        """
        Validate that the common clip file exists and is accessible.
        
        Updates the visual style of the input field based on validation result
        (green for valid, red for invalid).
        
        Args:
            event: Optional Tkinter event (for event binding)
            
        Returns:
            bool: True if file exists, False otherwise
            
        Complexity: O(1)
        Flow: Called on focus out, selection, or manual validation
        """
        path = self.common_clip_var.get()
        if path and os.path.isfile(path):
            self.common_clip_combo.configure(style="Valid.TCombobox")
            return True
        elif path:
            self.common_clip_combo.configure(style="Invalid.TCombobox")
            return False
        return False
    
    def validate_video_source_realtime(self, event: Optional[tk.Event] = None) -> bool:
        """
        Real-time validation for video source with debouncing.
        
        Implements a 500ms debounce to avoid excessive validation during typing.
        Cancels previous validation timer if still pending.
        
        Args:
            event: Optional Tkinter event (for event binding)
            
        Returns:
            bool: Always returns True (for event handling)
            
        Complexity: O(1)
        Flow: Called on each keystroke in video source field
        """
        # Cancel previous validation timer if exists
        if hasattr(self, '_video_source_timer'):
            self.after_cancel(self._video_source_timer)
        
        # Schedule validation after 500ms of no typing
        self._video_source_timer = self.after(500, self.validate_video_source)
        return True
    
    def validate_common_clip_realtime(self, event: Optional[tk.Event] = None) -> bool:
        """
        Real-time validation for common clip with debouncing.
        
        Implements a 500ms debounce to avoid excessive validation during typing.
        Cancels previous validation timer if still pending.
        
        Args:
            event: Optional Tkinter event (for event binding)
            
        Returns:
            bool: Always returns True (for event handling)
            
        Complexity: O(1)
        Flow: Called on each keystroke in common clip field
        """
        # Cancel previous validation timer if exists
        if hasattr(self, '_common_clip_timer'):
            self.after_cancel(self._common_clip_timer)
        
        # Schedule validation after 500ms of no typing
        self._common_clip_timer = self.after(500, self.validate_common_clip)
        return True
    
    def validate_fade_duration(self, event: Optional[tk.Event] = None) -> bool:
        """
        Validate fade duration is within acceptable range (0-10 seconds).
        
        Checks that the value is a valid number between 0 and 10.
        Shows tooltip with error message if invalid.
        
        Args:
            event: Optional Tkinter event (for event binding)
            
        Returns:
            bool: True if valid, False otherwise
            
        Complexity: O(1)
        Flow: Called on value change or focus out
        """
        try:
            value = self.fade_duration_var.get()
            if 0 <= value <= 10:
                self.fade_duration_spinbox.configure(style="Valid.TSpinbox")
                self.hide_tooltip()
                return True
            else:
                self.fade_duration_spinbox.configure(style="Invalid.TSpinbox")
                self.show_tooltip(self.fade_duration_spinbox,
                                "Fade duration must be between 0 and 10 seconds")
                return False
        except:
            self.fade_duration_spinbox.configure(style="Invalid.TSpinbox")
            self.show_tooltip(self.fade_duration_spinbox,
                            "Invalid number format")
            return False
    
    def validate_output_file(self, event: Optional[tk.Event] = None) -> bool:
        """
        Validate output file path and directory permissions.
        
        Checks:
        - File extension (warns if not .mp4)
        - Directory exists or can be created
        - Directory is writable
        
        Args:
            event: Optional Tkinter event (for event binding)
            
        Returns:
            bool: True if path is valid/writable, False otherwise
            
        Complexity: O(1)
        Flow: Called on focus out or path change
        """
        path = self.output_file_var.get()
        if path:
            # Check if directory is writable
            output_dir = os.path.dirname(path) or '.'
            
            # Check file extension
            if not path.endswith('.mp4'):
                self.output_file_combo.configure(style="Warning.TCombobox")
                self.show_tooltip(self.output_file_combo,
                                "Warning: Output should be .mp4 format")
                return True  # Warning, not error
            
            # Check if directory exists or can be created
            if os.path.exists(output_dir):
                if os.access(output_dir, os.W_OK):
                    self.output_file_combo.configure(style="Valid.TCombobox")
                    self.hide_tooltip()
                    return True
                else:
                    self.output_file_combo.configure(style="Invalid.TCombobox")
                    self.show_tooltip(self.output_file_combo,
                                    "Output directory is not writable")
                    return False
            else:
                # Directory doesn't exist, but might be creatable
                self.output_file_combo.configure(style="Warning.TCombobox")
                self.show_tooltip(self.output_file_combo,
                                "Output directory will be created")
                return True
        return False
    
    def validate_output_file_realtime(self, event: Optional[tk.Event] = None) -> bool:
        """
        Real-time validation for output file with debouncing.
        
        Implements a 500ms debounce to avoid excessive validation during typing.
        Cancels previous validation timer if still pending.
        
        Args:
            event: Optional Tkinter event (for event binding)
            
        Returns:
            bool: Always returns True (for event handling)
            
        Complexity: O(1)
        Flow: Called on each keystroke in output file field
        """
        # Cancel previous validation timer if exists
        if hasattr(self, '_output_file_timer'):
            self.after_cancel(self._output_file_timer)
        
        # Schedule validation after 500ms of no typing
        self._output_file_timer = self.after(500, self.validate_output_file)
        return True
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format for video sources.
        
        Checks if URL matches supported video platforms:
        - YouTube (youtube.com, youtu.be)
        - Vimeo (vimeo.com)
        - Dailymotion (dailymotion.com)
        
        Args:
            url: URL string to validate
            
        Returns:
            bool: True if URL format is valid, False otherwise
            
        Complexity: O(1) - regex matching
        Flow: Called by validate_video_source when URL detected
        """
        # Basic URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:www\.)?'  # optional www.
            r'(?:youtube\.com|youtu\.be|'  # YouTube domains
            r'vimeo\.com|dailymotion\.com)'  # Other supported sites
        )
        return bool(url_pattern.match(url))
    
    def show_tooltip(self, widget: tk.Widget, message: str) -> None:
        """
        Show a tooltip near the specified widget.
        
        Creates a temporary window with the message positioned near the widget.
        Auto-hides after 5 seconds.
        
        Args:
            widget: The widget to show tooltip near
            message: The tooltip message to display
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when validation fails or help needed
        """
        if hasattr(self, '_tooltip'):
            self.hide_tooltip()
        
        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        
        # Position tooltip near the widget
        x = widget.winfo_rootx() + widget.winfo_width() + 5
        y = widget.winfo_rooty() + widget.winfo_height() // 2
        self._tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self._tooltip, text=message,
                         background="lightyellow",
                         relief="solid",
                         borderwidth=1,
                         font=("Arial", 9))
        label.pack()
        
        # Auto-hide after 5 seconds
        self._tooltip.after(5000, self.hide_tooltip)
    
    def hide_tooltip(self) -> None:
        """
        Hide the current tooltip if one exists.
        
        Destroys the tooltip window and removes the reference.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called after timeout or when tooltip no longer needed
        """
        if hasattr(self, '_tooltip'):
            self._tooltip.destroy()
            delattr(self, '_tooltip')
    
    def check_disk_space(self) -> bool:
        """
        Check available disk space for output file.
        
        Warns user if less than 5GB free space available, as PowerHour
        videos can be 1-3GB in size.
        
        Returns:
            bool: True if sufficient space or user chooses to continue, False otherwise
            
        Complexity: O(1)
        Flow: Called during input validation before processing
        """
        output_path = self.output_file_var.get()
        if output_path:
            output_dir = os.path.dirname(output_path) or '.'
            if os.path.exists(output_dir):
                import shutil
                stats = shutil.disk_usage(output_dir)
                free_gb = stats.free / (1024 ** 3)
                
                # Warn if less than 5GB free
                if free_gb < 5:
                    self.log_warning(f"Low disk space: {free_gb:.1f} GB free")
                    return messagebox.askyesno(
                        "Low Disk Space",
                        f"Only {free_gb:.1f} GB free space available.\n"
                        "PowerHour videos can be 1-3 GB. Continue anyway?"
                    )
        return True
    
    def validate_all_inputs(self) -> bool:
        """
        Validate all inputs before starting video processing.
        
        Comprehensive validation including:
        - Video source exists/valid URL
        - Common clip file exists
        - Fade duration in valid range
        - Output directory writable
        - Sufficient disk space
        
        Shows error dialogs for any validation failures.
        
        Returns:
            bool: True if all inputs valid, False otherwise
            
        Complexity: O(1)
        Flow: Called by start_processing before beginning work
        """
        # Check video source
        if not self.video_source_var.get():
            messagebox.showerror("Input Error", "Please select a video source")
            return False
        
        if not self.validate_video_source():
            if self.video_source_var.get().startswith('http'):
                if not self.validate_url(self.video_source_var.get()):
                    messagebox.showerror("Input Error",
                                       "Invalid URL format. Supported: YouTube, Vimeo, Dailymotion")
                    return False
            else:
                messagebox.showerror("Input Error", "Invalid video source path")
                return False
        
        # Check common clip
        if not self.common_clip_var.get():
            messagebox.showerror("Input Error", "Please select a common clip")
            return False
        
        if not self.validate_common_clip():
            messagebox.showerror("Input Error", "Common clip file not found")
            return False
        
        # Check output file
        if not self.output_file_var.get():
            messagebox.showerror("Input Error", "Please specify an output file")
            return False
        
        # Validate fade duration
        if not self.validate_fade_duration():
            messagebox.showerror("Input Error",
                               "Fade duration must be between 0 and 10 seconds")
            return False
        
        # Check output directory is writable
        output_dir = os.path.dirname(self.output_file_var.get())
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Output Error", f"Cannot create output directory: {e}")
                return False
        
        # Check disk space
        if not self.check_disk_space():
            return False
        
        return True
    
    def start_processing(self) -> None:
        """
        Start video processing in a separate thread.
        
        Validates all inputs, disables UI controls, resets progress indicators,
        and launches the ProcessorThread to handle video generation.
        
        Returns:
            None
            
        Complexity: O(1) to start, O(n) for processing n videos
        Flow: Called when user clicks Start Processing button
        Dependencies: Requires ProcessorThread from powerhour_processor module
        """
        try:
            # Validate inputs first
            if not self.validate_all_inputs():
                return
            
            self.log_info("Starting video processing...")
            self.status_var.set("Processing...")
            self.start_button.config(state="disabled")
            self.cancel_button.config(state="normal")
            
            # Disable input fields during processing
            self.video_source_combo.config(state="disabled")
            self.common_clip_combo.config(state="disabled")
            self.fade_duration_spinbox.config(state="disabled")
            self.output_file_combo.config(state="disabled")
            
            # Reset progress bars
            self.current_progress_var.set(0)
            self.overall_progress_var.set(0)
            self.current_progress_label.config(text="0%")
            self.overall_progress_label.config(text="0/60 videos")
            self.eta_var.set("")
            
            # Prepare parameters
            params = {
                'video_source': self.video_source_var.get(),
                'common_clip': self.common_clip_var.get(),
                'fade_duration': self.fade_duration_var.get(),
                'output_file': self.output_file_var.get(),
                'video_quality': self.video_quality_var.get(),
                'audio_normalization': self.audio_normalization_var.get(),
                'output_format': self.output_format_var.get()
            }
            
            # Create and start processor thread
            self.processing_thread = ProcessorThread(self.message_queue, params)
            self.processing_thread.start()
            
            # Start time tracking for ETA
            self.processing_start_time = time.time()
            self.videos_processed = 0
            
        except Exception as e:
            self.handle_error(e, "Failed to start processing")
            self.reset_ui_state()
    
    def cancel_processing(self) -> None:
        """
        Cancel the current video processing operation.
        
        Prompts user for confirmation, then stops the processor thread
        and initiates cleanup. Waits for thread to fully stop before
        resetting UI state.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when user clicks Cancel button during processing
        """
        if messagebox.askyesno("Cancel Processing",
                               "Are you sure you want to cancel the current processing?"):
            self.log_warning("Cancelling processing...")
            self.status_var.set("Cancelling...")
            
            # Stop processor thread
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.stop()
                # Give thread time to clean up
                self.after(1000, self.check_thread_stopped)
            else:
                self.status_var.set("Cancelled")
                self.reset_ui_state()
    
    def check_thread_stopped(self) -> None:
        """
        Check if processing thread has stopped after cancellation.
        
        Recursively checks thread status every 500ms until thread stops.
        Resets UI state once thread has fully terminated.
        
        Returns:
            None
            
        Complexity: O(1) per check, O(n) total where n is number of checks
        Flow: Called after cancel_processing, recurses until thread stops
        """
        if self.processing_thread and self.processing_thread.is_alive():
            # Thread still running, check again
            self.after(500, self.check_thread_stopped)
        else:
            self.status_var.set("Cancelled")
            self.reset_ui_state()
            self.log_info("Processing cancelled")
    
    def on_processing_complete(self) -> None:
        """
        Handle successful processing completion.
        
        Updates recent items lists, saves configuration, resets UI state,
        and shows completion message to user.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when processing thread sends completion message
        """
        self.log_info("Processing complete!")
        self.status_var.set("Complete")
        
        # Add items to recent lists
        self.add_to_recent('sources', self.video_source_var.get())
        self.add_to_recent('common_clips', self.common_clip_var.get())
        self.add_to_recent('outputs', self.output_file_var.get())
        
        # Save configuration
        self.save_config()
        
        # Reset UI state
        self.reset_ui_state()
        
        # Show completion message
        messagebox.showinfo("Processing Complete",
                           "Your PowerHour video has been generated successfully!")
    
    def reset_ui_state(self) -> None:
        """
        Reset UI controls to their initial enabled/disabled state.
        
        Re-enables input fields and Start button, disables Cancel button.
        Used after processing completes or is cancelled.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called after processing completes, cancels, or errors
        """
        self.start_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.video_source_combo.config(state="normal")
        self.common_clip_combo.config(state="normal")
        self.fade_duration_spinbox.config(state="normal")
        self.output_file_combo.config(state="normal")
    
    def process_queue(self) -> None:
        """
        Process messages from the thread communication queue.
        
        Continuously checks for messages from the processing thread and
        updates the UI accordingly. Handles progress updates, status messages,
        logs, errors, and completion notifications.
        
        Message types handled:
        - 'progress': Update overall progress
        - 'status': Update status message
        - 'log': Add message to log
        - 'video_progress': Update current video progress
        - 'complete': Processing finished
        - 'error': Processing error occurred
        
        Returns:
            None
            
        Complexity: O(m) where m is number of messages in queue
        Flow: Called every 100ms via after() scheduling
        """
        try:
            while True:
                message = self.message_queue.get_nowait()
                
                if message['type'] == 'progress':
                    # Update progress bars
                    current = message.get('current', 0)
                    total = message.get('total', 60)
                    self.overall_progress_var.set(current)
                    self.overall_progress_label.config(text=f"{current}/{total} videos")
                    self.videos_processed = current
                    
                    # Update ETA and speed
                    self.update_eta(current, total)
                    self.update_processing_speed(current)
                    
                elif message['type'] == 'status':
                    # Update status
                    status = message['message']
                    self.status_var.set(status)
                    self.operation_label.config(text=status)
                    self.update_processing_stage(status)
                    
                elif message['type'] == 'log':
                    # Add to log
                    level = message.get('level', 'info')
                    msg = message['message']
                    if level == 'warning':
                        self.log_warning(msg)
                    elif level == 'error':
                        self.log_error(msg)
                    else:
                        self.log_info(msg)
                    
                    # Update current file if mentioned
                    if 'Processing:' in msg or 'Analyzing:' in msg:
                        filename = msg.split(':')[-1].strip() if ':' in msg else ""
                        if filename:
                            self.current_file_label.config(text=filename[:50])
                        
                elif message['type'] == 'video_progress':
                    # Update current video progress
                    percent = message.get('percent', 0)
                    self.current_progress_var.set(percent)
                    self.current_progress_label.config(text=f"{percent:.0f}%")
                    
                elif message['type'] == 'complete':
                    # Processing complete
                    self.on_processing_complete()
                    
                elif message['type'] == 'error':
                    # Show error
                    error_msg = message['message']
                    self.log_error(error_msg)
                    self.log_to_file("error", f"Processing error: {error_msg}")
                    
                    # Get user-friendly message
                    user_msg = self.get_user_friendly_error("ProcessingError", error_msg, "Video processing")
                    self.show_error_dialog("Processing Error", user_msg)
                    
                    self.status_var.set("Error")
                    self.reset_ui_state()
                    self.cleanup_temp_files()
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.after(100, self.process_queue)
    
    def update_processing_speed(self, current: int) -> None:
        """
        Update the processing speed indicator.
        
        Calculates videos processed per minute based on elapsed time.
        Maintains a rolling average of the last 10 measurements.
        
        Args:
            current: Number of videos processed so far
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when overall progress updates
        """
        if current > 0 and self.processing_start_time:
            elapsed = time.time() - self.processing_start_time
            videos_per_minute = (current / elapsed) * 60
            self.processing_speed.append(videos_per_minute)
            
            # Keep only last 10 measurements for average
            if len(self.processing_speed) > 10:
                self.processing_speed.pop(0)
            
            avg_speed = sum(self.processing_speed) / len(self.processing_speed)
            self.speed_label.config(text=f"{avg_speed:.1f} videos/minute")
    
    def update_processing_stage(self, status: str) -> None:
        """
        Update the processing stage label based on status message.
        
        Maps status keywords to user-friendly stage descriptions:
        - Initializing → lightblue
        - Downloading → yellow
        - Analyzing → orange
        - Processing/Encoding → green
        - Concatenating/Finalizing → blue
        - Complete → dark green
        
        Args:
            status: Status message from processing thread
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when status messages are received
        """
        stage_map = {
            "Initializing": ("Initializing", "lightblue"),
            "Downloading": ("Downloading", "yellow"),
            "Analyzing": ("Analyzing", "orange"),
            "Processing": ("Encoding", "green"),
            "Concatenating": ("Finalizing", "blue"),
            "Complete": ("Complete", "darkgreen")
        }
        
        for key, (stage, color) in stage_map.items():
            if key in status:
                self.processing_stage_label.config(text=stage)
                # Could add color if using a Canvas widget
                break
    
    def update_eta(self, current: int, total: int) -> None:
        """
        Update ETA (Estimated Time to Arrival) based on processing speed.
        
        Calculates remaining time based on average time per video so far.
        Formats as "~X minutes Y seconds remaining".
        
        Args:
            current: Number of videos processed
            total: Total number of videos to process
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when progress updates
        """
        if current > 0 and hasattr(self, 'processing_start_time'):
            elapsed = time.time() - self.processing_start_time
            avg_time_per_video = elapsed / current
            remaining_videos = total - current
            eta_seconds = remaining_videos * avg_time_per_video
            
            # Format ETA
            if eta_seconds > 0:
                minutes = int(eta_seconds / 60)
                seconds = int(eta_seconds % 60)
                if minutes > 0:
                    self.eta_var.set(f"~{minutes} minutes {seconds} seconds remaining")
                else:
                    self.eta_var.set(f"~{seconds} seconds remaining")
    
    def setup_styles(self) -> None:
        """
        Setup custom TTK styles for validation indicators.
        
        Creates custom styles for Entry, Spinbox, and Combobox widgets:
        - Valid (green): Input is valid
        - Invalid (red): Input has errors
        - Warning (orange): Input has warnings but may proceed
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called during application startup
        """
        style = ttk.Style()
        
        # Valid entry style (green border)
        style.map("Valid.TEntry",
                 fieldbackground=[("focus", "lightgreen"), ("!focus", "white")],
                 bordercolor=[("focus", "green"), ("!focus", "green")])
        
        # Invalid entry style (red border)
        style.map("Invalid.TEntry",
                 fieldbackground=[("focus", "lightpink"), ("!focus", "white")],
                 bordercolor=[("focus", "red"), ("!focus", "red")])
        
        # Warning entry style (orange border)
        style.map("Warning.TEntry",
                 fieldbackground=[("focus", "lightyellow"), ("!focus", "white")],
                 bordercolor=[("focus", "orange"), ("!focus", "orange")])
        
        # Valid spinbox style
        style.map("Valid.TSpinbox",
                 fieldbackground=[("focus", "lightgreen"), ("!focus", "white")],
                 bordercolor=[("focus", "green"), ("!focus", "green")])
        
        # Invalid spinbox style
        style.map("Invalid.TSpinbox",
                 fieldbackground=[("focus", "lightpink"), ("!focus", "white")],
                 bordercolor=[("focus", "red"), ("!focus", "red")])
        
        # Combobox styles
        style.map("Valid.TCombobox",
                 fieldbackground=[("focus", "lightgreen"), ("!focus", "white")],
                 bordercolor=[("focus", "green"), ("!focus", "green")])
        
        style.map("Invalid.TCombobox",
                 fieldbackground=[("focus", "lightpink"), ("!focus", "white")],
                 bordercolor=[("focus", "red"), ("!focus", "red")])
        
        style.map("Warning.TCombobox",
                 fieldbackground=[("focus", "lightyellow"), ("!focus", "white")],
                 bordercolor=[("focus", "orange"), ("!focus", "orange")])


    def get_config_path(self) -> str:
        """
        Get the configuration file path based on the operating system.
        
        Platform-specific paths:
        - Windows: %APPDATA%/PowerHour/config.json
        - macOS: ~/Library/Application Support/PowerHour/config.json
        - Linux: ~/.config/PowerHour/config.json
        
        Creates directory if it doesn't exist.
        
        Returns:
            str: Full path to configuration file
            
        Complexity: O(1)
        Flow: Called during initialization
        """
        system = platform.system()
        
        if system == "Windows":
            config_dir = os.path.join(os.environ.get('APPDATA', ''), 'PowerHour')
        elif system == "Darwin":  # macOS
            config_dir = os.path.expanduser('~/Library/Application Support/PowerHour')
        else:  # Linux and others
            config_dir = os.path.expanduser('~/.config/PowerHour')
        
        # Create directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        return os.path.join(config_dir, 'config.json')
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration dictionary.
        
        Provides sensible defaults for all configuration options including
        recent items lists, default values, and window geometry.
        
        Returns:
            Dict[str, Any]: Default configuration dictionary
            
        Complexity: O(1)
        Flow: Called during initialization if no config exists
        """
        return {
            "recent_sources": [],
            "recent_outputs": [],
            "recent_common_clips": [],
            "default_fade_duration": 3.0,
            "last_video_source": "",
            "last_common_clip": "",
            "last_output_dir": "",
            "window_geometry": "800x600",
            "max_recent_items": 10
        }
    
    def load_config(self) -> None:
        """
        Load configuration from JSON file.
        
        Loads saved configuration and merges with defaults to ensure
        all required keys exist. Handles JSON decode errors gracefully.
        
        Returns:
            None
            
        Complexity: O(n) where n is size of config file
        Flow: Called during initialization
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self.app_config.update(loaded_config)
                    # Don't log during init - log_text widget doesn't exist yet
        except json.JSONDecodeError as e:
            # Don't log to UI during init - log_text widget doesn't exist yet
            self.log_to_file("error", f"Config load error: {e}")
        except Exception as e:
            # Don't log to UI during init - log_text widget doesn't exist yet
            self.log_to_file("error", f"Config load error: {e}")
    
    def save_config(self) -> None:
        """
        Save current configuration to JSON file.
        
        Updates configuration with current values and writes to disk.
        Saves window geometry, recent items, and user preferences.
        
        Returns:
            None
            
        Complexity: O(n) where n is size of configuration
        Flow: Called on window close and after processing completes
        """
        try:
            # Update current values
            self.app_config['last_video_source'] = self.video_source_var.get()
            self.app_config['last_common_clip'] = self.common_clip_var.get()
            
            output_path = self.output_file_var.get()
            if output_path:
                self.app_config['last_output_dir'] = os.path.dirname(output_path)
            
            self.app_config['default_fade_duration'] = self.fade_duration_var.get()
            
            # Save window geometry
            self.app_config['window_geometry'] = self.geometry()
            
            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(self.app_config, f, indent=4)
            
            if hasattr(self, 'log_text'):
                self.log_info("Configuration saved")
        except Exception as e:
            if hasattr(self, 'log_text'):
                self.log_warning(f"Could not save configuration: {e}")
            self.log_to_file("error", f"Config save error: {e}")
    
    def add_to_recent(self, list_name: str, item: str) -> None:
        """
        Add an item to a recent items list.
        
        Maintains recent items lists with most recent first, removes
        duplicates, and limits to max_recent_items (default 10).
        Updates corresponding combo box values.
        
        Args:
            list_name: Name of list ('sources', 'common_clips', or 'outputs')
            item: Item to add to the list
            
        Returns:
            None
            
        Complexity: O(n) where n is length of recent list
        Flow: Called after successful processing
        """
        if not item:
            return
        
        key = f'recent_{list_name}'
        recent_list = self.app_config.get(key, [])
        
        # Remove if already exists (to move to front)
        if item in recent_list:
            recent_list.remove(item)
        
        # Add to front
        recent_list.insert(0, item)
        
        # Limit list size
        max_items = self.app_config.get('max_recent_items', 10)
        recent_list = recent_list[:max_items]
        
        # Update config
        self.app_config[key] = recent_list
        
        # Update combo box values
        if list_name == 'sources':
            self.video_source_combo['values'] = recent_list
        elif list_name == 'common_clips':
            self.common_clip_combo['values'] = recent_list
        elif list_name == 'outputs':
            self.output_file_combo['values'] = recent_list
    
    def on_closing(self) -> None:
        """
        Handle window closing event.
        
        Saves configuration including current settings, performs cleanup
        of temporary files, logs shutdown, and destroys window.
        
        Returns:
            None
            
        Complexity: O(n) where n is number of temp files
        Flow: Called when user closes window or application exits
        """
        try:
            # Save additional settings
            self.app_config['video_quality'] = self.video_quality_var.get()
            self.app_config['audio_normalization'] = self.audio_normalization_var.get()
            self.app_config['output_format'] = self.output_format_var.get()
            self.app_config['expert_mode'] = self.expert_mode_var.get()
            
            self.save_config()
            self.cleanup_temp_files()
            self.log_to_file("info", "Application closed normally")
        except Exception as e:
            self.log_to_file("error", f"Error during shutdown: {e}")
        finally:
            self.destroy()
    
    # Enhanced Features Methods (Phase 6)
    
    def toggle_expert_mode(self) -> None:
        """
        Toggle expert mode on/off.
        
        Shows or hides advanced options panel with FFmpeg parameter editing.
        Updates status bar hint when toggled.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when Expert Mode menu item is toggled
        """
        if self.expert_mode_var.get():
            # Show expert controls
            self.expert_frame.grid(row=6, column=0, columnspan=3,
                                 sticky="ew", padx=5, pady=5)
            self.log_info("Expert mode enabled")
            self.hint_label.config(text="Expert mode: Advanced options available")
        else:
            # Hide expert controls
            self.expert_frame.grid_forget()
            self.log_info("Expert mode disabled")
            self.hint_label.config(text="Ready to create PowerHour videos")
    
    def save_preset(self) -> None:
        """
        Save current settings as a named preset.
        
        Prompts user for preset name and saves current configuration
        values (fade duration, quality, normalization, format) for
        later reuse.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called from Presets menu
        """
        from tkinter import simpledialog
        preset_name = simpledialog.askstring("Save Preset",
                                            "Enter preset name:")
        if preset_name:
            preset = {
                'fade_duration': self.fade_duration_var.get(),
                'video_quality': self.video_quality_var.get(),
                'audio_normalization': self.audio_normalization_var.get(),
                'output_format': self.output_format_var.get()
            }
            
            # Save to presets in config
            if 'presets' not in self.app_config:
                self.app_config['presets'] = {}
            self.app_config['presets'][preset_name] = preset
            self.save_config()
            
            self.log_info(f"Preset '{preset_name}' saved")
            messagebox.showinfo("Preset Saved", f"Preset '{preset_name}' saved successfully")
    
    def load_preset(self) -> None:
        """
        Load a previously saved preset.
        
        Shows dialog with list of saved presets for user selection.
        Applies selected preset values to current settings.
        
        Returns:
            None
            
        Complexity: O(n) where n is number of saved presets
        Flow: Called from Presets menu
        """
        if 'presets' not in self.app_config or not self.app_config['presets']:
            messagebox.showinfo("No Presets", "No saved presets found")
            return
        
        # Create preset selection dialog
        preset_window = tk.Toplevel(self)
        preset_window.title("Load Preset")
        preset_window.geometry("300x200")
        
        ttk.Label(preset_window, text="Select a preset:").pack(pady=10)
        
        preset_var = tk.StringVar()
        preset_list = tk.Listbox(preset_window, height=6)
        for name in self.app_config['presets'].keys():
            preset_list.insert(tk.END, name)
        preset_list.pack(pady=10)
        
        def load_selected():
            selection = preset_list.curselection()
            if selection:
                preset_name = preset_list.get(selection[0])
                self.apply_saved_preset(preset_name)
                preset_window.destroy()
        
        ttk.Button(preset_window, text="Load", command=load_selected).pack()
    
    def apply_preset(self, preset_type: str) -> None:
        """
        Apply a built-in preset configuration.
        
        Built-in presets:
        - 'party': Medium quality, fast processing
        - 'archive': High quality, slower processing
        - 'fast': Low quality, fastest processing
        
        Args:
            preset_type: Type of preset to apply
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called from Presets menu
        """
        presets = {
            'party': {
                'fade_duration': 2.0,
                'video_quality': 'medium',
                'audio_normalization': True,
                'output_format': 'mp4'
            },
            'archive': {
                'fade_duration': 3.0,
                'video_quality': 'high',
                'audio_normalization': True,
                'output_format': 'mkv'
            },
            'fast': {
                'fade_duration': 1.0,
                'video_quality': 'low',
                'audio_normalization': False,
                'output_format': 'mp4'
            }
        }
        
        if preset_type in presets:
            preset = presets[preset_type]
            self.fade_duration_var.set(preset['fade_duration'])
            self.video_quality_var.set(preset['video_quality'])
            self.audio_normalization_var.set(preset['audio_normalization'])
            self.output_format_var.set(preset['output_format'])
            
            self.log_info(f"Applied {preset_type} preset")
    
    def apply_saved_preset(self, preset_name: str) -> None:
        """
        Apply a saved user preset by name.
        
        Loads preset values from configuration and applies them to
        current settings.
        
        Args:
            preset_name: Name of the saved preset
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called by load_preset after selection
        """
        if preset_name in self.app_config.get('presets', {}):
            preset = self.app_config['presets'][preset_name]
            self.fade_duration_var.set(preset.get('fade_duration', 3.0))
            self.video_quality_var.set(preset.get('video_quality', 'medium'))
            self.audio_normalization_var.set(preset.get('audio_normalization', True))
            self.output_format_var.set(preset.get('output_format', 'mp4'))
            
            self.log_info(f"Loaded preset '{preset_name}'")
    
    def show_about(self) -> None:
        """
        Show About dialog with application information.
        
        Displays version, description, and copyright information
        in a message box.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called from Help menu
        """
        about_text = """PowerHour Video Generator
Version 1.0
        
Create PowerHour videos with ease!
        
A PowerHour is a drinking game where participants
take a shot of beer every minute for an hour,
typically accompanied by 60 one-minute video clips.
        
This tool automates the creation of these videos
with transitions and audio normalization.
        
© 2024 - Built with Python and FFmpeg"""
        
        messagebox.showinfo("About PowerHour", about_text)
    
    def show_user_guide(self) -> None:
        """
        Show user guide in a scrollable window.
        
        Displays comprehensive user guide with step-by-step instructions,
        tips, and troubleshooting information.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called from Help menu
        """
        guide = """PowerHour Video Generator - User Guide
        
1. SELECT VIDEO SOURCE
   - Choose a folder with video files
   - Or paste a YouTube playlist URL
   
2. CHOOSE COMMON CLIP
   - Select a transition video
   - Plays between each main clip
   
3. SET FADE DURATION
   - Controls transition smoothness
   - 0-10 seconds
   
4. SPECIFY OUTPUT
   - Choose where to save
   - MP4 format recommended
   
5. CLICK START
   - Processing takes 10-30 minutes
   - Watch progress in real-time
   
TIPS:
- Need at least 60 videos for full hour
- Smaller files process faster
- Close other programs for speed"""
        
        # Create scrollable text window
        guide_window = tk.Toplevel(self)
        guide_window.title("User Guide")
        guide_window.geometry("500x400")
        
        text = ScrolledText(guide_window, wrap=tk.WORD)
        text.pack(fill="both", expand=True)
        text.insert("1.0", guide)
        text.config(state="disabled")
    
    def show_shortcuts(self) -> None:
        """
        Show keyboard shortcuts reference.
        
        Displays a dialog listing all available keyboard shortcuts
        for quick reference.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called from Help menu
        """
        shortcuts = """Keyboard Shortcuts:
        
Ctrl+O    - Browse for video source
Ctrl+S    - Save output as
Ctrl+R    - Start processing
Ctrl+C    - Cancel processing
Ctrl+L    - Clear log
Ctrl+Q    - Quit application
        
F1        - Show help
F5        - Refresh validation
F11       - Toggle expert mode"""
        
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def view_error_log(self) -> None:
        """
        Open error log file in system default text editor.
        
        Platform-specific:
        - Windows: Uses os.startfile()
        - macOS: Uses 'open' command
        - Linux: Uses 'xdg-open' command
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called from Help menu
        """
        import subprocess
        import platform
        
        if os.path.exists(self.error_log_file):
            system = platform.system()
            if system == "Windows":
                os.startfile(self.error_log_file)
            elif system == "Darwin":  # macOS
                subprocess.call(["open", self.error_log_file])
            else:  # Linux
                subprocess.call(["xdg-open", self.error_log_file])
        else:
            messagebox.showinfo("No Error Log", "No error log file found")
    
    def check_updates(self) -> None:
        """
        Check for application updates.
        
        Currently shows static version information. In production,
        would check remote server for updates.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called from Help menu
        """
        # In a real app, this would check a server
        messagebox.showinfo("Check for Updates",
                          "You are running the latest version (1.0)")
    
    def update_resource_usage(self) -> None:
        """
        Update CPU and RAM usage display in status bar.
        
        Uses psutil library if available to show current system
        resource usage. Updates every 2 seconds.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called every 2 seconds via after() scheduling
        """
        # Check if psutil is available (it's imported as optional at the top)
        if psutil is not None:
            try:
                # Get CPU and memory usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                mem_percent = memory.percent
                
                self.resource_label.config(
                    text=f"CPU: {cpu_percent:.0f}% | RAM: {mem_percent:.0f}%"
                )
            except Exception:
                # Error getting resource usage
                pass
        
        # Schedule next update
        self.after(2000, self.update_resource_usage)
    
    def add_tooltip(self, widget: tk.Widget, text: str) -> None:
        """
        Add a hover tooltip to a widget.
        
        Creates tooltip that appears on mouse hover and disappears
        on mouse leave. Used for providing contextual help.
        
        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text to display
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called during UI construction for help text
        """
        def on_enter(event):
            self.tooltip = tk.Toplevel()
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(self.tooltip, text=text,
                           background="lightyellow",
                           relief="solid", borderwidth=1,
                           font=("Arial", 9))
            label.pack()
        
        def on_leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                del self.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    # Error Handling Methods (Phase 5)
    
    def setup_exception_handler(self) -> None:
        """
        Set up global exception handler for uncaught exceptions.
        
        Installs a custom sys.excepthook that logs exceptions to file
        and shows user-friendly error dialogs. Allows KeyboardInterrupt
        to pass through for debugging.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called once during initialization
        """
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            error_msg = ''.join(traceback.format_exception(
                exc_type, exc_value, exc_traceback
            ))
            
            self.log_to_file("critical", f"Uncaught exception:\n{error_msg}")
            
            # Show error dialog
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}\n\n"
                "Please check the error log for details."
            )
        
        sys.excepthook = handle_exception
    
    def handle_error(self, error: Exception, context: str = "") -> str:
        """
        Handle an error with logging and user notification.
        
        Logs full error details to file, maps to user-friendly message,
        and displays in GUI log. Returns the user-friendly message.
        
        Args:
            error: The exception that occurred
            context: Optional context about where error occurred
            
        Returns:
            str: User-friendly error message
            
        Complexity: O(1)
        Flow: Called when exceptions occur during operation
        """
        error_msg = str(error)
        error_type = type(error).__name__
        
        # Log full error details
        full_error = traceback.format_exc()
        self.log_to_file("error", f"{context}\n{full_error}")
        
        # Map to user-friendly message
        user_msg = self.get_user_friendly_error(error_type, error_msg, context)
        
        # Show in GUI log
        self.log_error(f"{context}: {user_msg}")
        
        # Return the user message
        return user_msg
    
    def get_user_friendly_error(self, error_type: str, error_msg: str, context: str) -> str:
        """
        Map technical error messages to user-friendly explanations.
        
        Provides clear, actionable error messages for common issues
        like missing dependencies, permission errors, disk space, etc.
        
        Args:
            error_type: Type/class name of the error
            error_msg: The error message string
            context: Context where error occurred
            
        Returns:
            str: User-friendly error message
            
        Complexity: O(1)
        Flow: Called by handle_error for message mapping
        """
        error_map = {
            "FileNotFoundError": "The specified file or folder could not be found.",
            "PermissionError": "Permission denied. Please check file permissions.",
            "OSError": "System error occurred. Please check disk space and permissions.",
            "JSONDecodeError": "Configuration file is corrupted. Using defaults.",
            "subprocess.CalledProcessError": "Video processing failed. Check FFmpeg installation.",
            "MemoryError": "Out of memory. Try processing fewer videos.",
            "KeyboardInterrupt": "Operation cancelled by user.",
            "ValueError": "Invalid input value provided.",
            "IOError": "Input/output error. Check disk space and file access.",
        }
        
        # Check for specific error patterns
        if "ffmpeg" in error_msg.lower():
            return "FFmpeg error. Please ensure FFmpeg is installed correctly."
        elif "ffprobe" in error_msg.lower():
            return "FFprobe error. Please ensure FFprobe is installed correctly."
        elif "yt-dlp" in error_msg.lower():
            return "YouTube download error. Please check the URL and internet connection."
        elif "disk" in error_msg.lower() or "space" in error_msg.lower():
            return "Insufficient disk space. Please free up space and try again."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            return "Network error. Please check your internet connection."
        
        # Return mapped message or generic
        return error_map.get(error_type, f"{error_type}: {error_msg}")
    
    def show_error_dialog(self, title: str, message: str, details: Optional[str] = None) -> None:
        """
        Show an error dialog box with optional details.
        
        Args:
            title: Dialog title
            message: Main error message
            details: Optional detailed error information
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when errors need user attention
        """
        if details:
            full_message = f"{message}\n\nDetails:\n{details}"
        else:
            full_message = message
        
        messagebox.showerror(title, full_message)
    
    def get_error_log_path(self) -> str:
        """
        Get the path to the error log file.
        
        Places error log in same directory as config file for
        centralized application data storage.
        
        Returns:
            str: Full path to error.log file
            
        Complexity: O(1)
        Flow: Called during initialization
        """
        config_dir = os.path.dirname(self.get_config_path())
        return os.path.join(config_dir, 'error.log')
    
    def log_to_file(self, level: str, message: str) -> None:
        """
        Log message to error log file with timestamp.
        
        Appends timestamped log entries to error.log file.
        Automatically rotates log when it exceeds 10MB.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Message to log
            
        Returns:
            None
            
        Complexity: O(1) average, O(n) when rotating large log
        Flow: Called throughout application for persistent logging
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
            
            # Create log file if needed
            os.makedirs(os.path.dirname(self.error_log_file), exist_ok=True)
            
            # Append to log file
            with open(self.error_log_file, 'a') as f:
                f.write(log_entry)
                
            # Rotate log if too large (>10MB)
            if os.path.getsize(self.error_log_file) > 10 * 1024 * 1024:
                self.rotate_log_file()
                
        except Exception:
            # Silent fail - don't want logging to cause errors
            pass
    
    def rotate_log_file(self) -> None:
        """
        Rotate log file when it exceeds size limit (10MB).
        
        Renames current log to .old, removing previous .old if exists.
        Prevents unbounded log growth.
        
        Returns:
            None
            
        Complexity: O(n) where n is file size
        Flow: Called by log_to_file when size exceeds limit
        """
        try:
            # Rename current log to .old
            old_log = self.error_log_file + '.old'
            if os.path.exists(old_log):
                os.remove(old_log)
            os.rename(self.error_log_file, old_log)
        except Exception:
            pass
    
    def cleanup_temp_files(self) -> None:
        """
        Clean up temporary files and directories.
        
        Removes:
        - Tracked temporary files from processing
        - PowerHour temporary directories in system temp
        
        Handles errors silently to avoid cleanup failures affecting
        application shutdown.
        
        Returns:
            None
            
        Complexity: O(n) where n is number of temp files
        Flow: Called on exit and after processing errors
        """
        try:
            # Clean tracked temp files
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        if os.path.isdir(temp_file):
                            import shutil
                            shutil.rmtree(temp_file)
                        else:
                            os.remove(temp_file)
                except Exception:
                    pass
            
            self.temp_files.clear()
            
            # Clean system temp PowerHour directories
            temp_dir = tempfile.gettempdir()
            for item in os.listdir(temp_dir):
                if item.startswith('powerhour_') or item.startswith('tmp_powerhour_'):
                    try:
                        full_path = os.path.join(temp_dir, item)
                        if os.path.isdir(full_path):
                            import shutil
                            shutil.rmtree(full_path)
                    except Exception:
                        pass
                        
        except Exception as e:
            self.log_to_file("error", f"Cleanup error: {e}")
    
    def cleanup_on_exit(self) -> None:
        """
        Perform cleanup operations on application exit.
        
        Registered with atexit to ensure cleanup happens even on
        unexpected termination. Calls cleanup_temp_files silently.
        
        Returns:
            None
            
        Complexity: O(n) where n is number of temp files
        Flow: Called automatically on application exit
        """
        try:
            self.cleanup_temp_files()
        except Exception:
            pass
    
    def add_temp_file(self, path: str) -> None:
        """
        Add a file or directory path to cleanup list.
        
        Tracks temporary files created during processing for
        cleanup on exit or error.
        
        Args:
            path: File or directory path to track for cleanup
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when temporary files are created
        """
        if path not in self.temp_files:
            self.temp_files.append(path)


def main() -> None:
    """
    Main entry point for the GUI application.
    
    Creates the PowerHourGUI instance, sets up styles, displays
    initial messages, and starts the Tkinter event loop.
    
    Returns:
        None
        
    Complexity: O(1)
    Flow: Called when script is run directly
    """
    app = PowerHourGUI()
    app.setup_styles()
    
    # Initial log message
    app.log_info("PowerHour Video Generator GUI initialized")
    app.log_info("Select your video source, common clip, and output settings to begin")
    
    app.mainloop()


if __name__ == "__main__":
    main()