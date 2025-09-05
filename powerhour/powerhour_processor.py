"""
PowerHour Video Processor

Modified version of powerhour_generator.py for GUI integration with
threading support and queue-based communication for progress updates.

This module provides the ProcessorThread class that handles the actual
video processing work in a separate thread, allowing the GUI to remain
responsive during lengthy operations. It processes video files, applies
audio normalization, adds fade effects, and concatenates everything
into a final PowerHour video.

Classes:
    ProcessorThread: Thread class for video processing with GUI communication

Dependencies:
    - ffmpeg: For video processing and encoding
    - ffprobe: For video analysis
    - yt-dlp (optional): For downloading online playlists

Author: Anthony Izzo
Version: 1.0.0
License: MIT
"""

import os
import sys
import shutil
import random
import subprocess
import json
from glob import glob
from tempfile import TemporaryDirectory
from datetime import datetime
import threading
import queue
import time
from typing import Optional, Dict, List, Tuple, Any, Union


class ProcessorThread(threading.Thread):
    """
    Thread class for processing videos with GUI communication.
    
    Handles the complete video processing pipeline in a separate thread,
    including video analysis, audio normalization, fade effects, and
    concatenation. Communicates with the GUI through a message queue
    for real-time progress updates and error reporting.
    
    Attributes:
        message_queue (queue.Queue): Queue for sending messages to GUI
        params (Dict[str, Any]): Processing parameters from GUI
        stop_event (threading.Event): Event for cancellation signaling
        daemon (bool): Thread runs as daemon for clean shutdown
        
    Methods:
        run: Main processing execution
        stop: Cancel processing
        send_*: Various message sending methods
        
    Complexity: O(n*m) where n is number of videos, m is video processing time
    """
    
    def __init__(self, message_queue: queue.Queue, params: Dict[str, Any]) -> None:
        """
        Initialize the processor thread with configuration.
        
        Sets up the thread for video processing with parameters from the GUI
        and establishes communication through the provided message queue.
        
        Args:
            message_queue: Queue for sending progress/status messages to GUI
            params: Dictionary containing processing parameters:
                - video_source (str): Path to video folder or playlist URL
                - common_clip (str): Path to transition clip file
                - fade_duration (float): Fade in/out duration in seconds
                - output_file (str): Path for final output video
                - video_quality (str): Quality preset (low/medium/high)
                - audio_normalization (bool): Whether to normalize audio
                - output_format (str): Output container format
                
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called by GUI when user starts processing
        """
        super().__init__()
        self.message_queue = message_queue
        self.params = params
        self.stop_event = threading.Event()
        self.daemon = True
        
    def run(self) -> None:
        """
        Main processing thread execution.
        
        Executes the complete video processing pipeline:
        1. Validates inputs and dependencies
        2. Downloads videos if URL provided
        3. Analyzes audio loudness
        4. Processes individual clips with effects
        5. Concatenates into final PowerHour video
        
        Sends status updates and progress through message queue.
        Handles exceptions gracefully with error reporting.
        
        Returns:
            None
            
        Complexity: O(n*m) where n is videos, m is processing per video
        Flow: Called automatically when thread.start() is invoked
        """
        try:
            # Send initial status
            self.send_status("Initializing processing...")
            self.send_log("info", "Starting PowerHour video generation")
            
            # Validate inputs
            if not self._validate_inputs():
                return
            
            # Check dependencies
            if not self._check_dependencies():
                return
            
            # Start processing
            self._process_videos()
            
        except Exception as e:
            self.send_error(f"Processing error: {str(e)}")
            self.send_log("error", f"Fatal error: {str(e)}")
        
    def stop(self) -> None:
        """
        Stop the processing thread gracefully.
        
        Sets the stop event to signal cancellation to all processing
        operations. Processing loops check this event and exit cleanly.
        
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when user clicks Cancel button
        """
        self.stop_event.set()
        self.send_log("warning", "Processing cancelled by user")
        
    def _validate_inputs(self) -> bool:
        """
        Validate input parameters before processing.
        
        Checks that all required files exist and paths are valid.
        Sends appropriate error messages if validation fails.
        
        Returns:
            bool: True if all inputs valid, False otherwise
            
        Complexity: O(1)
        Flow: Called at start of run() method
        """
        self.send_status("Validating inputs...")
        
        # Check video source
        video_source = self.params.get('video_source', '')
        if not video_source:
            self.send_error("No video source specified")
            return False
            
        if not video_source.startswith('http') and not os.path.exists(video_source):
            self.send_error(f"Video source not found: {video_source}")
            return False
        
        # Check common clip
        common_clip = self.params.get('common_clip', '')
        if not common_clip or not os.path.exists(common_clip):
            self.send_error(f"Common clip not found: {common_clip}")
            return False
        
        self.send_log("info", "Input validation successful")
        return True
    
    def _check_dependencies(self) -> bool:
        """
        Check for required external dependencies.
        
        Verifies that ffmpeg, ffprobe, and optionally yt-dlp are
        installed and accessible in the system PATH.
        
        Returns:
            bool: True if all dependencies found, False otherwise
            
        Complexity: O(1)
        Flow: Called after input validation
        """
        self.send_status("Checking dependencies...")
        
        # Check for ffmpeg
        if shutil.which('ffmpeg') is None:
            self.send_error("FFmpeg is not installed. Please install FFmpeg to continue.")
            return False
        
        # Check for ffprobe
        if shutil.which('ffprobe') is None:
            self.send_error("FFprobe is not installed. Please install FFprobe to continue.")
            return False
        
        # Check for yt-dlp if URL provided
        if self.params.get('video_source', '').startswith('http'):
            if shutil.which('yt-dlp') is None:
                self.send_error("yt-dlp is not installed. Please install yt-dlp for URL support.")
                return False
        
        self.send_log("info", "All dependencies found")
        return True
    
    def _process_videos(self) -> None:
        """
        Main video processing logic coordinator.
        
        Orchestrates the entire processing pipeline:
        - Handles URL downloads if needed
        - Scans for video files
        - Processes each video with effects
        - Concatenates into final output
        
        Returns:
            None
            
        Complexity: O(n*m) where n is videos, m is processing time
        Flow: Called after validation and dependency checks
        """
        video_folder = self.params.get('video_source')
        common_clip = self.params.get('common_clip')
        fade_duration = self.params.get('fade_duration', 3.0)
        output_file = self.params.get('output_file')
        
        with TemporaryDirectory() as temp_dir:
            # Handle URL download if needed
            if video_folder.startswith('http'):
                self.send_status("Downloading playlist...")
                self.send_log("info", f"Downloading from: {video_folder}")
                
                if not self._download_playlist(video_folder, temp_dir):
                    return
                    
                video_folder = temp_dir
            
            # Get video files
            self.send_status("Scanning video files...")
            video_files = self._get_video_files(video_folder)
            
            if not video_files:
                self.send_error("No video files found in the specified directory")
                return
            
            # Process videos
            self._process_video_files(
                video_files, common_clip, fade_duration, 
                output_file, temp_dir
            )
    
    def _download_playlist(self, url: str, temp_dir: str) -> bool:
        """
        Download playlist/videos using yt-dlp.
        
        Downloads videos from supported platforms (YouTube, Vimeo, etc.)
        to a temporary directory for processing. Monitors download progress
        and can be cancelled via stop_event.
        
        Args:
            url: Playlist or video URL to download
            temp_dir: Temporary directory path for downloads
            
        Returns:
            bool: True if download successful, False otherwise
            
        Complexity: O(n*s) where n is videos, s is download size
        Flow: Called when video_source is a URL
        """
        command = [
            "yt-dlp", "-o", f"{temp_dir}/%(title)s.%(ext)s",
            "--yes-playlist", url
        ]
        
        try:
            log_file = os.path.join(temp_dir, 'yt-dlp.log')
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    command, 
                    stdout=subprocess.PIPE, 
                    stderr=log,
                    text=True
                )
                
                # Monitor download progress
                for line in process.stdout:
                    if self.stop_event.is_set():
                        process.terminate()
                        return False
                    
                    # Parse progress if available
                    if '[download]' in line:
                        self.send_log("info", line.strip())
                
                process.wait()
                
                if process.returncode != 0:
                    self.send_error("Failed to download playlist")
                    return False
                    
        except Exception as e:
            self.send_error(f"Download error: {str(e)}")
            return False
        
        return True
    
    def _get_video_files(self, folder: str) -> List[str]:
        """
        Get list of video files from folder.
        
        Scans folder for video files, excludes non-video extensions,
        and randomly samples up to 60 videos if more are available.
        
        Args:
            folder: Directory path to scan for videos
            
        Returns:
            List[str]: List of video file paths (max 60)
            
        Complexity: O(n) where n is files in directory
        Flow: Called after download or with local folder
        """
        excluded_extensions = ['.log', '.py', '.txt', '.json']
        video_files = []
        
        for file in glob(os.path.join(folder, '*')):
            if os.path.splitext(file)[1].lower() not in excluded_extensions:
                video_files.append(file)
        
        # Randomly select up to 60 videos
        max_videos = 60
        if len(video_files) > max_videos:
            video_files = random.sample(video_files, max_videos)
        
        self.send_log("info", f"Found {len(video_files)} video files")
        return video_files
    
    def _process_video_files(self, video_files: List[str], common_clip: str,
                            fade_duration: float, output_file: str,
                            temp_dir: str) -> None:
        """
        Process video files and create final output.
        
        Handles the core processing:
        1. Analyzes audio loudness for normalization
        2. Re-encodes each video with effects
        3. Processes common transition clip
        4. Concatenates all clips into final video
        
        Args:
            video_files: List of video file paths to process
            common_clip: Path to transition clip
            fade_duration: Fade effect duration in seconds
            output_file: Path for final output video
            temp_dir: Temporary working directory
            
        Returns:
            None
            
        Complexity: O(n*m) where n is videos, m is encoding time
        Flow: Main processing coordinator method
        """
        ffmpeg_logs_dir = os.path.join(temp_dir, 'logs')
        loudness_json_dir = os.path.join(temp_dir, 'loudness_json')
        os.makedirs(ffmpeg_logs_dir, exist_ok=True)
        os.makedirs(loudness_json_dir, exist_ok=True)
        
        # Analyze common clip loudness
        self.send_status("Analyzing common clip...")
        common_clip_log = os.path.join(ffmpeg_logs_dir, 'common_clip.log')
        self._analyze_loudness(common_clip, common_clip_log, loudness_json_dir)
        
        # Check video durations and analyze loudness
        self.send_status("Analyzing video files...")
        valid_videos = []
        total_videos = len(video_files)
        
        for i, video_file in enumerate(video_files, 1):
            if self.stop_event.is_set():
                return
            
            # Update progress
            self.send_progress(i, total_videos)
            self.send_status(f"Analyzing video {i}/{total_videos}")
            
            duration = self._get_video_duration(video_file)
            if duration and duration >= 80:
                log_file = os.path.join(ffmpeg_logs_dir, f'loudness_{i:04d}.log')
                self._analyze_loudness(video_file, log_file, loudness_json_dir)
                valid_videos.append((video_file, duration))
            
            self.send_video_progress((i / total_videos) * 100)
        
        if not valid_videos:
            self.send_error("No valid videos found (need duration >= 80 seconds)")
            return
        
        self.send_log("info", f"Processing {len(valid_videos)} valid videos")
        
        # Re-encode common clip
        self.send_status("Processing common clip...")
        common_clip_temp = os.path.join(temp_dir, 'common_clip.mp4')
        common_clip_json = os.path.join(
            loudness_json_dir, 
            os.path.basename(common_clip) + '_loudness.json'
        )
        
        if not self._reencode_video(
            common_clip, 0, fade_duration, common_clip_temp,
            os.path.join(ffmpeg_logs_dir, 'common_clip.log'),
            fade_duration, common_clip_json
        ):
            self.send_error("Failed to process common clip")
            return
        
        # Process each video
        self.send_status("Processing videos...")
        clip_list = []
        failed = 0
        
        for i, (video_file, duration) in enumerate(valid_videos, 1):
            if self.stop_event.is_set():
                return
            
            self.send_progress(i, len(valid_videos))
            self.send_status(f"Processing video {i}/{len(valid_videos)}")
            
            # Random start time
            start_time = random.randint(10, int(duration) - 70)
            temp_clip_name = f'temp_clip_{i:04d}.mp4'
            temp_clip_path = os.path.join(temp_dir, temp_clip_name)
            json_loudness_file = os.path.join(
                loudness_json_dir,
                os.path.basename(video_file) + '_loudness.json'
            )
            
            if self._reencode_video(
                video_file, start_time, 60, temp_clip_path,
                os.path.join(ffmpeg_logs_dir, f'video_{i:04d}.log'),
                fade_duration, json_loudness_file
            ):
                clip_list.append(temp_clip_path)
                self.send_log("info", f"Processed: {os.path.basename(video_file)}")
            else:
                self.send_log("warning", f"Failed: {os.path.basename(video_file)}")
                failed += 1
            
            self.send_video_progress((i / len(valid_videos)) * 100)
        
        if failed > 0:
            self.send_log("warning", f"{failed} files failed to process")
        
        # Concatenate videos
        self.send_status("Creating final video...")
        self.send_log("info", "Concatenating clips...")
        
        concat_list_path = os.path.join(temp_dir, 'concat_list.txt')
        with open(concat_list_path, 'w') as concat_file:
            for i, clip_path in enumerate(clip_list):
                if i > 0:  # Add common clip before each video except the first
                    concat_file.write(f"file '{common_clip_temp}'\n")
                concat_file.write(f"file '{clip_path}'\n")
        
        # Final concatenation
        concat_command = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_list_path, '-c', 'copy', output_file
        ]
        
        if self._run_command(
            concat_command, 
            os.path.join(ffmpeg_logs_dir, 'concat.log')
        ):
            self.send_log("info", f"Output saved to: {output_file}")
            self.send_complete(output_file)
        else:
            self.send_error("Failed to concatenate videos")
    
    def _get_video_duration(self, video_file: str) -> Optional[float]:
        """
        Get duration of a video file using ffprobe.
        
        Extracts video duration in seconds for validation and
        random start time calculation.
        
        Args:
            video_file: Path to video file
            
        Returns:
            Optional[float]: Duration in seconds, None if error
            
        Complexity: O(1) - ffprobe metadata read
        Flow: Called during video analysis phase
        """
        try:
            duration = subprocess.check_output([
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of',
                'default=noprint_wrappers=1:nokey=1', video_file
            ], text=True).strip()
            
            if duration == 'N/A':
                return None
            return float(duration)
        except subprocess.CalledProcessError:
            return None
    
    def _analyze_loudness(self, video_file: str, log_file: str,
                         json_output_dir: str) -> None:
        """
        Analyze audio loudness for normalization.
        
        Uses ffmpeg's loudnorm filter to analyze audio characteristics
        and saves the results as JSON for use during re-encoding.
        This enables proper audio normalization across all clips.
        
        Args:
            video_file: Path to video file to analyze
            log_file: Path to save processing log
            json_output_dir: Directory to save loudness JSON
            
        Returns:
            None
            
        Complexity: O(n) where n is video duration
        Flow: Called before re-encoding each video
        """
        ffmpeg_command = [
            'ffmpeg', '-i', video_file, '-af',
            'loudnorm=I=-23:LRA=7:print_format=json',
            '-f', 'null', '-'
        ]
        
        try:
            output = subprocess.check_output(
                ffmpeg_command, 
                stderr=subprocess.STDOUT, 
                text=True
            )
            
            # Parse JSON from output
            loudness_info = None
            json_data = ""
            capturing = False
            
            for line in output.splitlines():
                if '{' in line:
                    capturing = True
                    json_data = line[line.find('{'):]
                elif capturing:
                    json_data += line
                    if '}' in line:
                        try:
                            loudness_info = json.loads(json_data)
                            break
                        except json.JSONDecodeError:
                            pass
            
            if loudness_info:
                # Save loudness info
                json_file_name = os.path.basename(video_file) + '_loudness.json'
                json_file_path = os.path.join(json_output_dir, json_file_name)
                with open(json_file_path, 'w') as json_file:
                    json.dump(loudness_info, json_file, indent=4)
                    
        except subprocess.CalledProcessError as e:
            with open(log_file, 'w') as log:
                log.write(str(e.output))
    
    def _reencode_video(self, video_file: str, start_time: float,
                       duration: float, output_path: str, log_file: str,
                       fade_duration: float, json_loudness_file: str) -> bool:
        """
        Re-encode video with audio normalization and fade effects.
        
        Processes a video segment with:
        - Audio loudness normalization for consistent volume
        - Fade in/out effects for smooth transitions
        - Resolution scaling to 1280x720
        - Frame rate normalization to 30fps
        - H.264 encoding with AAC audio
        
        Args:
            video_file: Source video file path
            start_time: Start time in seconds for clip extraction
            duration: Clip duration in seconds
            output_path: Path for encoded output
            log_file: Path for ffmpeg log
            fade_duration: Duration of fade effects in seconds
            json_loudness_file: Path to loudness analysis JSON
            
        Returns:
            bool: True if encoding successful, False otherwise
            
        Complexity: O(n) where n is video duration
        Flow: Called for each video clip during processing
        """
        fade_in_start = 0
        fade_out_start = max(duration - fade_duration, 0)
        
        # Load loudness info if available
        try:
            with open(json_loudness_file, 'r') as f:
                audio_loudness = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            audio_loudness = {}
        
        audio_filters = (
            f"loudnorm=I=-23:LRA=7:TP=-1.5:"
            f"measured_I={audio_loudness.get('input_i', '-23.0')}:"
            f"measured_LRA={audio_loudness.get('input_lra', '7.0')}:"
            f"measured_TP={audio_loudness.get('input_tp', '-1.5')}:"
            f"measured_thresh={audio_loudness.get('input_thresh', '-50.0')}:"
            f"offset={audio_loudness.get('target_offset', '0.0')}:"
            f"linear=true:print_format=summary"
        )
        
        ffmpeg_command = [
            'ffmpeg', '-y', '-ss', str(start_time), '-t', str(duration),
            '-i', video_file,
            '-vf', f"scale=1280:720, fade=t=in:st={fade_in_start}:d={fade_duration}, "
                   f"fade=t=out:st={fade_out_start}:d={fade_duration}",
            '-af', audio_filters,
            '-r', '30', '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output_path
        ]
        
        return self._run_command(ffmpeg_command, log_file)
    
    def _run_command(self, command: List[str], log_file: str) -> bool:
        """
        Run a shell command and log output.
        
        Executes external commands (primarily ffmpeg) with error
        handling and logging. Suppresses stdout but logs stderr
        for debugging.
        
        Args:
            command: Command and arguments as list
            log_file: Path to save command output
            
        Returns:
            bool: True if command succeeded (exit code 0), False otherwise
            
        Complexity: O(1) for execution, varies by command
        Flow: Called by various processing methods
        """
        try:
            with open(log_file, 'w') as log:
                result = subprocess.run(
                    command, 
                    stdout=subprocess.DEVNULL,
                    stderr=log
                )
            return result.returncode == 0
        except Exception as e:
            with open(log_file, 'a') as log:
                log.write(f"\nError: {str(e)}")
            return False
    
    # Queue message methods for GUI communication
    
    def send_progress(self, current: int, total: int) -> None:
        """
        Send overall progress update to GUI.
        
        Updates the main progress bar showing X/60 videos completed.
        
        Args:
            current: Number of videos processed
            total: Total number of videos to process
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called after each video is processed
        """
        self.message_queue.put({
            'type': 'progress',
            'current': current,
            'total': total
        })
    
    def send_status(self, message: str) -> None:
        """
        Send status message update to GUI.
        
        Updates the status label with current operation description.
        
        Args:
            message: Status message to display
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called at each major processing stage
        """
        self.message_queue.put({
            'type': 'status',
            'message': message
        })
    
    def send_log(self, level: str, message: str) -> None:
        """
        Send log message to GUI log display.
        
        Adds a message to the scrolling log with appropriate
        color coding based on level.
        
        Args:
            level: Log level ('info', 'warning', 'error')
            message: Log message text
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called throughout processing for logging
        """
        self.message_queue.put({
            'type': 'log',
            'level': level,
            'message': message
        })
    
    def send_error(self, message: str) -> None:
        """
        Send error message to GUI.
        
        Reports processing errors that will stop execution.
        GUI will display error dialog and reset UI state.
        
        Args:
            message: Error message describing the problem
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when unrecoverable errors occur
        """
        self.message_queue.put({
            'type': 'error',
            'message': message
        })
    
    def send_video_progress(self, percent: float) -> None:
        """
        Send current video progress percentage.
        
        Updates the current video progress bar (0-100%).
        
        Args:
            percent: Progress percentage (0.0 to 100.0)
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called during individual video processing
        """
        self.message_queue.put({
            'type': 'video_progress',
            'percent': percent
        })
    
    def send_complete(self, output_file: str) -> None:
        """
        Send processing completion message.
        
        Notifies GUI that processing finished successfully.
        GUI will show completion dialog and reset state.
        
        Args:
            output_file: Path to the generated video file
            
        Returns:
            None
            
        Complexity: O(1)
        Flow: Called when all processing completes successfully
        """
        self.message_queue.put({
            'type': 'complete',
            'output_file': output_file
        })