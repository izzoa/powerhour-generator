#!/usr/bin/env python3
"""
Debug runner for PowerHour GUI with enhanced error logging.
This script helps diagnose startup issues by providing detailed error information.
"""

import sys
import traceback
import os

# Add parent directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_with_debug():
    """Run the GUI with enhanced error catching and logging."""
    print("=" * 60)
    print("PowerHour GUI Debug Runner")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")
    print(f"Current directory: {os.getcwd()}")
    print("=" * 60)
    
    try:
        print("Step 1: Importing powerhour_gui module...")
        from powerhour import powerhour_gui
        print("✓ Module imported successfully")
        
        print("\nStep 2: Creating PowerHourGUI instance...")
        app = powerhour_gui.PowerHourGUI()
        print("✓ GUI instance created successfully")
        
        print("\nStep 3: Setting up styles...")
        app.setup_styles()
        print("✓ Styles configured successfully")
        
        print("\nStep 4: Adding initial log messages...")
        app.log_info("PowerHour Video Generator GUI initialized")
        app.log_info("Select your video source, common clip, and output settings to begin")
        print("✓ Initial messages logged")
        
        print("\nStep 5: Starting main event loop...")
        print("GUI window should now be visible.\n")
        print("=" * 60)
        app.mainloop()
        
    except TypeError as e:
        print("\n❌ TypeError encountered!")
        print(f"Error message: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Try to identify which object is being called as a function
        tb = traceback.extract_tb(sys.exc_info()[2])
        for frame in tb:
            print(f"\nFrame: {frame.filename}:{frame.lineno}")
            print(f"Function: {frame.name}")
            print(f"Line: {frame.line}")
            
        sys.exit(1)
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)
    
    print("\nGUI closed normally.")

if __name__ == "__main__":
    run_with_debug()