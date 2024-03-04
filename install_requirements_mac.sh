#!/bin/bash

# Check for Homebrew, install if we don't have it
if test ! $(which brew); then
    echo "Installing homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
fi

# Update and upgrade any existing brew installations
echo "Updating and upgrading Homebrew..."
brew update
brew upgrade

# Install Python 3
echo "Checking for Python 3 installation..."
if test ! $(which python3); then
    echo "Installing Python 3..."
    brew install python
else
    echo "Python 3 is already installed."
fi

# Install ffmpeg
echo "Checking for ffmpeg installation..."
if test ! $(which ffmpeg); then
    echo "Installing ffmpeg..."
    brew install ffmpeg
else
    echo "ffmpeg is already installed."
fi

# Install yt-dlp
echo "Checking for yt-dlp installation..."
if test ! $(which yt-dlp); then
    echo "Installing yt-dlp..."
    brew install yt-dlp
else
    echo "yt-dlp is already installed."
fi

echo "All prerequisite components are installed."
