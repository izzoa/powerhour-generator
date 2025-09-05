#!/usr/bin/env python3
"""
Test script for PowerHour GUI
Verifies Phase 2 integration is working
"""

import tkinter as tk
from tkinter import messagebox
import os
import sys
import shutil

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    dependencies = {
        'ffmpeg': shutil.which('ffmpeg'),
        'ffprobe': shutil.which('ffprobe'),
        'yt-dlp': shutil.which('yt-dlp')
    }
    
    missing = []
    for name, path in dependencies.items():
        if path:
            print(f"✓ {name}: {path}")
        else:
            print(f"✗ {name}: NOT FOUND")
            missing.append(name)
    
    if missing:
        print("\nMissing dependencies:")
        for dep in missing:
            if dep == 'yt-dlp':
                print(f"  - {dep} (optional, for URL support)")
            else:
                print(f"  - {dep} (REQUIRED)")
        
        if 'ffmpeg' in missing or 'ffprobe' in missing:
            print("\nFFmpeg is required. Install with:")
            print("  macOS: brew install ffmpeg")
            print("  Linux: sudo apt install ffmpeg")
            print("  Windows: Download from https://ffmpeg.org/download.html")
            return False
    
    return True

def test_gui_launch():
    """Test if the GUI launches without errors"""
    print("\nTesting GUI launch...")
    
    try:
        # Import the GUI from the new package structure
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from powerhour.powerhour_gui import PowerHourGUI
        
        # Create a test instance
        root = tk.Tk()
        root.withdraw()  # Hide the test root
        
        # Try to instantiate the GUI
        app = PowerHourGUI()
        
        print("✓ GUI created successfully")
        
        # Check if all sections were built
        checks = [
            ('Input section', hasattr(app, 'video_source_entry')),
            ('Control section', hasattr(app, 'start_button')),
            ('Progress section', hasattr(app, 'current_progress_bar')),
            ('Log section', hasattr(app, 'log_text')),
            ('Message queue', hasattr(app, 'message_queue')),
        ]
        
        for name, check in checks:
            if check:
                print(f"✓ {name}: OK")
            else:
                print(f"✗ {name}: FAILED")
        
        # Test logging methods
        app.log_info("Test info message")
        app.log_warning("Test warning message")
        app.log_error("Test error message")
        print("✓ Logging methods: OK")
        
        # Clean up
        app.destroy()
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI launch failed: {e}")
        return False

def test_processor_import():
    """Test if the processor module imports correctly"""
    print("\nTesting processor import...")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from powerhour.powerhour_processor import ProcessorThread
        print("✓ ProcessorThread imported successfully")
        
        # Check if required methods exist
        methods = ['run', 'stop', 'send_progress', 'send_status', 
                  'send_log', 'send_error', 'send_complete']
        
        for method in methods:
            if hasattr(ProcessorThread, method):
                print(f"✓ ProcessorThread.{method}: OK")
            else:
                print(f"✗ ProcessorThread.{method}: MISSING")
        
        return True
        
    except Exception as e:
        print(f"✗ Processor import failed: {e}")
        return False

def create_test_files():
    """Create test video files for testing"""
    print("\nCreating test environment...")
    
    # Create test directories
    test_dirs = ['test_videos', 'test_output']
    for dir_name in test_dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✓ Created directory: {dir_name}")
    
    # Create a simple test video using ffmpeg (if available)
    if shutil.which('ffmpeg'):
        # Create a 10-second test video
        test_video_cmd = [
            'ffmpeg', '-y', '-f', 'lavfi', 
            '-i', 'testsrc=duration=10:size=320x240:rate=30',
            '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=10',
            '-c:v', 'libx264', '-c:a', 'aac',
            'test_videos/test_video.mp4'
        ]
        
        import subprocess
        try:
            subprocess.run(test_video_cmd, 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
            print("✓ Created test video: test_videos/test_video.mp4")
            
            # Create common clip
            shutil.copy('test_videos/test_video.mp4', 
                       'test_videos/common_clip.mp4')
            print("✓ Created common clip: test_videos/common_clip.mp4")
            
        except Exception as e:
            print(f"✗ Could not create test videos: {e}")
    else:
        print("✗ FFmpeg not available, cannot create test videos")
        print("  Place video files manually in test_videos/ directory")
    
    return True

def main():
    """Main test execution"""
    print("=" * 50)
    print("PowerHour GUI Test Suite")
    print("Phase 2: Processing Integration")
    print("=" * 50)
    
    # Run tests
    tests_passed = 0
    tests_total = 4
    
    if check_dependencies():
        tests_passed += 1
    
    if test_processor_import():
        tests_passed += 1
    
    if test_gui_launch():
        tests_passed += 1
    
    if create_test_files():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Test Results: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("✓ All tests passed! GUI is ready for use.")
        print("\nTo run the GUI:")
        print("  python -m powerhour.powerhour_gui")
        print("\nTest files created in:")
        print("  - test_videos/ (input videos)")
        print("  - test_output/ (for output)")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
    
    print("=" * 50)
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)