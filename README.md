# Powerhour Generator 

Create your own custom powerhour mixes effortlessly. You can either provide a folder of music videos or a YouTube playlist link. If the latter, this tool will download the playlist using yt-dlp (if a playlist URL is given) and randomly extract one-minute clips from each video, seamlessly stitching them together with fade-in and fade-out effects. An interstitial video of your choosing can be inserted between each clip for a personalized touch.  

The script ensures that all videos are re-encoded to the same format, resolution, framerate, and codecs before concatenation. This means you can input virtually any video format that FFmpeg supports, and it will output a standardized x264-encoded video, perfect for any gathering.

Let the party begin!  

## Features   

- Processes a directory of video files or downloads a YouTube playlist. 
- Inserts a common clip between each video.  
- Re-encodes videos to a uniform format, resolution, and framerate.   
- Normalizes audio levels across all clips.  
- Ensures clips are taken at least 10 seconds away from the start and end of their source videos to avoid spoilers or abrupt beginnings/ends.
- Randomizes video selection.   
- Supports specifying the number of videos (default is 60 for an hour-long powerhour).  
- Includes a progress bar during processing for better user experience.  

## Installation  

This script requires Python 3, ffmpeg, and yt-dlp.  

### Linux   

For Debian/Ubuntu Linux, you can install the dependencies using the provided `install_requirements.sh` script:   

```  
chmod +x install_requirements.sh
sudo ./install_requirements.sh  
```

This will install Python 3 if missing, install ffmpeg, and install yt-dlp via pip.   

For other Linux distributions, you may need to install the dependencies manually using your distribution's package manager.   

### Windows Installation

1. Open PowerShell as Administrator 
   - Press the Windows key and search for "PowerShell"
   - Right-click on PowerShell and select "Run as Administrator"
2. Download the `Install-Requirements.ps1` script
   - You can download it directly in PowerShell using:
     ```
     Invoke-WebRequest -Uri https://raw.githubusercontent.com/amizzo87/powerhour-generator/main/Install_Requirements_Win.ps1 -OutFile Install-Requirements.ps1
     ```
   - Or browse to this GitHub repo and manually download the file to a chosen directory
3. Give Execution Permissions to the Script
   - Run the command: 
     ```
     Unblock-File .\Install-Requirements.ps1
     ```
4. Execute the Script
   - Run the command:
     ```
     .\Install-Requirements.ps1
     ```
   - This will install Chocolatey if missing and then install Python 3, ffmpeg, and yt-dlp
5. Verify Installations
   - Run the following commands and check that version strings are printed:
     ```
     python --version
     ffmpeg -version
     yt-dlp --version
     ```

### MacOS   

For Mac systems, use the provided `install_requirements.sh` script to install dependencies via Homebrew:  

```  
chmod +x install_requirements.sh  
./install_requirements.sh
```

This will:  

- Install Homebrew if missing  
- Update and upgrade Homebrew packages    
- Install or upgrade Python 3  
- Install or upgrade ffmpeg  
- Install or upgrade yt-dlp  

### Verifying Installation   

After running the setup script, you can verify the installations with:   

```
python3 --version   
ffmpeg -version   
yt-dlp --version  
```

This will print out version strings if installed correctly.   

If you encounter any issues, you may need to install components manually via your system's package manager.  

## Usage  

Execute the script from the command line, supplying the path to the video folder or a YouTube playlist URL, the path to the common clip, the fade duration in seconds, and the desired output file name as arguments.  

```bash  
python powerhour_generator.py [/path/to/video/folder OR playlist_url] /path/to/common_clip.mp4 fade_duration_in_seconds output_file_name.mp4   
```

## Arguments   

- `/path/to/video/folder OR playlist_url`: Directory containing the video files to be processed or a YouTube playlist URL.  
- `/path/to/common_clip.mp4`: Path to the video file that will be inserted between each content video.   
- `fade_duration_in_seconds`: Duration of the fade effect applied to the common clip and at the beginning and end of each video clip (in seconds).  
- `output_file_name.mp4`: Filename for the output concatenated video.   

## How It Works  

1. If a YouTube playlist URL is provided, the script downloads the playlist using yt-dlp.   
2. The script checks the duration of each video file in the provided directory or downloaded playlist to ensure it meets the minimum duration requirement, considering additional buffers to avoid selecting clips too close to the start or end of the videos.  
3. It analyzes and normalizes the audio loudness across all videos to ensure a consistent audio experience.   
4. The common clip and each video file are re-encoded to the same resolution, framerate, and codecs.  
5. The script then randomly selects videos (up to the specified maximum limit), processes them by inserting the common clip between each, and ensures audio levels are normalized.   
6. Finally, all processed clips are concatenated into a single output file, ready to be played.   

## Troubleshooting   

If you run into issues with the progress bar or any other feature, verify that you're running the script in a standard terminal or command prompt environment. Some IDEs or text editors may not support the in-place line updates required for the progress bar functionality. If you're having trouble downloading a YouTube playlist, ensure that yt-dlp is installed and updated to the latest version.

Let me know if you have any other questions!
