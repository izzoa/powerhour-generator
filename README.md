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

## Setup

Before using the Powerhour Generator, you need to ensure that Python 3.x, FFmpeg, and yt-dlp are installed on your system. To simplify this process, we've provided an `install_requirements.sh` script for macOS users.

### Running the `install_requirements.sh` Script

1. Open Terminal on your Mac.
2. Navigate to the directory containing the `install_requirements.sh` script.
3. Make the script executable by running the command:
   ```bash
   chmod +x install_requirements.sh
   ```
4. Execute the script to automatically install the necessary components:
   ```bash
   ./install_requirements.sh
   ```

The script checks for and installs Homebrew (if not already installed), Python 3, FFmpeg, and yt-dlp.

### Manual Installation

If you prefer to manually install the prerequisites or are using a different operating system, please ensure the following are installed:
- **Python 3.x**: Ensure Python 3.x is installed and accessible in your system's PATH.
- **FFmpeg**: Required for processing videos.
- **[yt-dlp (Optional)](https://github.com/yt-dlp/yt-dlp)**: Needed if you wish to download YouTube playlists. Ensure it's in your system's PATH.

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
