#!/usr/bin/env python3
"""
Setup script for PowerHour Generator

This script configures the PowerHour Generator package for distribution
and installation via pip or other Python package managers.
"""

from setuptools import setup, find_packages
from pathlib import Path
import sys

# Ensure we're using Python 3.8 or higher
if sys.version_info < (3, 8):
    sys.exit('PowerHour Generator requires Python 3.8 or higher.')

# Read the README file for the long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read version from a dedicated version file or extract from main module
VERSION = '1.0.0'

setup(
    name='powerhour-generator',
    version=VERSION,
    author='Anthony Izzo',
    author_email='anthony@izzo.one',
    description='A powerful video compilation tool for creating 60-minute PowerHour videos with GUI and CLI interfaces',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/izzoa/powerhour-generator',
    project_urls={
        'Bug Tracker': 'https://github.com/izzoa/powerhour-generator/issues',
        'Documentation': 'https://github.com/izzoa/powerhour-generator/wiki',
        'Source Code': 'https://github.com/izzoa/powerhour-generator',
    },
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Video :: Conversion',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Environment :: X11 Applications',
        'Environment :: Win32 (MS Windows)',
        'Environment :: MacOS X',
    ],
    keywords='video, powerhour, ffmpeg, gui, compilation, generator, multimedia',
    
    # Package discovery
    packages=find_packages(exclude=['tests', 'tests.*', 'docs', 'docs.*']),
    
    # Python version requirement
    python_requires='>=3.8',
    
    # Core dependencies
    install_requires=[
        # GUI requirements
        # Note: tkinter is included with Python, no need to list it
        
        # Optional but recommended
        'Pillow>=9.0.0',  # For image handling in GUI
        
        # For better file dialogs on some systems
        'pyperclip>=1.8.0',  # Clipboard support
    ],
    
    # Optional dependencies for additional features
    extras_require={
        'youtube': [
            'yt-dlp>=2023.1.1',  # For YouTube/playlist support
        ],
        'dev': [
            'pytest>=7.0.0',  # Testing framework
            'pytest-cov>=4.0.0',  # Coverage reporting
            'black>=22.0.0',  # Code formatter
            'flake8>=5.0.0',  # Linting
            'mypy>=1.0.0',  # Type checking
            'sphinx>=5.0.0',  # Documentation generator
            'sphinx-rtd-theme>=1.0.0',  # Documentation theme
        ],
        'build': [
            'pyinstaller>=5.0',  # For creating executables
            'wheel>=0.37.0',  # For building wheels
            'twine>=4.0.0',  # For uploading to PyPI
        ],
    },
    
    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'powerhour=powerhour.powerhour_generator:main',
            'powerhour-cli=powerhour.powerhour_generator:main',
        ],
        'gui_scripts': [
            'powerhour-gui=powerhour.powerhour_gui:main',
        ],
    },
    
    # Include additional files
    package_data={
        '': [
            '*.md',
            '*.txt',
            '*.json',
            'LICENSE',
        ],
    },
    
    # Include data files (currently commented out until desktop files are created)
    data_files=[
        # ('share/applications', ['data/powerhour-generator.desktop']),  # Linux desktop file
        # ('share/icons/hicolor/256x256/apps', ['assets/logo.png']),  # App icon
    ],
    
    # Don't zip the egg file for better debugging
    zip_safe=False,
    
    # Include package data in distribution
    include_package_data=True,
    
    # Platform-specific dependencies
    # Note: FFmpeg must be installed separately as it's not a Python package
    
    # Test suite
    test_suite='tests',
)

# Post-installation message
def post_install_message():
    """Display important information after installation"""
    print("\n" + "="*60)
    print("PowerHour Generator Installation Complete!")
    print("="*60)
    print("\nIMPORTANT: External Dependencies Required")
    print("-"*40)
    print("1. FFmpeg and FFprobe must be installed separately:")
    print("   - Windows: Download from https://ffmpeg.org/download.html")
    print("   - macOS: Install via 'brew install ffmpeg'")
    print("   - Linux: Install via 'sudo apt-get install ffmpeg' or equivalent")
    print("\n2. For YouTube support, install with:")
    print("   pip install powerhour-generator[youtube]")
    print("\nUsage:")
    print("   GUI Mode: powerhour-gui")
    print("   CLI Mode: powerhour [options]")
    print("\nDocumentation: https://github.com/izzoa/powerhour-generator")
    print("="*60 + "\n")

# Call post-installation message if running setup
if __name__ == '__main__' and 'install' in sys.argv:
    from atexit import register
    register(post_install_message)