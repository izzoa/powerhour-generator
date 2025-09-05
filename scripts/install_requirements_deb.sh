#!/bin/bash

# Update package lists
echo "Updating package lists..."
sudo apt update

# Install Python 3 if not already installed
echo "Checking for Python 3 installation..."
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    sudo apt install -y python3
else
    echo "Python 3 is already installed."
fi

# Install ffmpeg
echo "Checking for ffmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    sudo apt install -y ffmpeg
else
    echo "ffmpeg is already installed."
fi

# Install yt-dlp using Python3 pip
echo "Checking for yt-dlp installation..."
if ! command -v yt-dlp &> /dev/null; then
    echo "Installing yt-dlp..."
    sudo python3 -m pip install yt-dlp
else
    echo "yt-dlp is already installed."
fi

echo "All prerequisite components are installed."
