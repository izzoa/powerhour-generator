# -*- mode: python ; coding: utf-8 -*-
"""
PowerHour Generator PyInstaller Specification File

This spec file configures PyInstaller to build standalone executables
for the PowerHour Generator application.

Build commands:
    Windows: pyinstaller powerhour.spec
    macOS: pyinstaller powerhour.spec
    Linux: pyinstaller powerhour.spec
"""

import sys
import os
from pathlib import Path

# Determine if we're building for Windows
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Get the current directory
SPEC_DIR = Path(os.path.dirname(os.path.abspath(SPEC)))

# Analysis configuration
a = Analysis(
    # Main script
    ['powerhour/powerhour_gui.py'],
    
    # Additional paths to search for imports
    pathex=[str(SPEC_DIR), str(SPEC_DIR / 'powerhour')],
    
    # Binary files to include
    binaries=[],
    
    # Data files to include
    datas=[
        # Include documentation
        ('README.md', '.'),
        ('docs/README_GUI.md', 'docs'),
        ('docs/USER_GUIDE.md', 'docs'),
        ('docs/CHANGELOG.md', 'docs'),
        ('LICENSE', '.'),
        ('assets/logo.png', 'assets'),
        
        # Include any config templates or sample files
        # ('data/config_template.json', 'data'),
    ],
    
    # Hidden imports that PyInstaller might miss
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'json',
        'threading',
        'queue',
        'subprocess',
        'pathlib',
        'datetime',
        'tempfile',
        'shutil',
        'urllib.parse',
        'configparser',
        'platform',
        'powerhour.powerhour_processor',
        'powerhour.powerhour_generator',
    ],
    
    # Hooks
    hookspath=[],
    hooksconfig={},
    
    # Runtime hooks
    runtime_hooks=[],
    
    # Packages to exclude
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'notebook',
        'jupyter',
        'IPython',
    ],
    
    # Win/Mac specific
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    
    # Cipher (set to None for no encryption)
    cipher=None,
    
    # Don't freeze these modules
    noarchive=False,
)

# PYZ archive (Python ZIP)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# Executable configuration
exe_kwargs = {
    'name': 'PowerHourGenerator',
    'pyz': pyz,
    'a.scripts': a.scripts,
    'a.binaries': a.binaries,
    'a.zipfiles': a.zipfiles,
    'a.datas': a.datas,
    'exclude_binaries': True,
    'debug': False,
    'bootloader_ignore_signals': False,
    'strip': False,
    'upx': True,
    'console': False,  # Set to True if you want a console window
    'disable_windowed_traceback': False,
    'argv_emulation': False,
    'target_arch': None,
    'codesign_identity': None,
    'entitlements_file': None,
}

# Platform-specific settings
if IS_WINDOWS:
    exe_kwargs.update({
        'icon': 'assets/logo.png' if Path('assets/logo.png').exists() else None,
        'version_file': 'version_info.txt' if Path('version_info.txt').exists() else None,
        'uac_admin': False,  # Set to True if admin rights needed
    })
elif IS_MACOS:
    exe_kwargs.update({
        'icon': 'assets/logo.png' if Path('assets/logo.png').exists() else None,
    })
else:  # Linux
    exe_kwargs.update({
        'icon': 'assets/logo.png' if Path('assets/logo.png').exists() else None,
    })

# Create the executable
exe = EXE(**exe_kwargs)

# Collection configuration for one-folder distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PowerHourGenerator',
)

# macOS-specific: Create app bundle
if IS_MACOS:
    app = BUNDLE(
        coll,
        name='PowerHourGenerator.app',
        icon='assets/logo.png' if Path('assets/logo.png').exists() else None,
        bundle_identifier='com.powerhour.generator',
        info_plist={
            'CFBundleName': 'PowerHour Generator',
            'CFBundleDisplayName': 'PowerHour Generator',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'CFBundleExecutable': 'PowerHourGenerator',
            'CFBundleIconFile': 'powerhour-icon.icns',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
            'NSRequiresAquaSystemAppearance': 'False',  # Support dark mode
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Video Files',
                    'CFBundleTypeRole': 'Viewer',
                    'CFBundleTypeExtensions': ['mp4', 'avi', 'mkv', 'mov'],
                }
            ],
        },
    )

# Build notes
print("""
========================================
PowerHour Generator Build Configuration
========================================

Platform: {platform}
Mode: GUI Application (windowed)
Output: dist/PowerHourGenerator/

Post-Build Steps:
1. Test the executable on a clean system
2. Verify FFmpeg is available or bundled
3. Package with installer (optional)

For different build options:
- Console mode: Set console=True in exe_kwargs
- Debug build: Set debug=True in exe_kwargs
- Single file: Use --onefile flag

========================================
""".format(platform=sys.platform))