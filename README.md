# Powerhour Generator

Create your own custom powerhour mixes effortlessly. Provide a folder full of your favorite music videos, and this tool will randomly extract one-minute clips from each, seamlessly stitching them together with fade-in and fade-out effects. An interstitial video of your choosing can be inserted between each clip for a personalized touch.

The script ensures that all videos are re-encoded to the same format, resolution, framerate, and codecs before concatenation. This means you can input virtually any video format that FFmpeg supports, and it will output a standardized x264-encoded video, perfect for any gathering.

Let the party begin!

## Features

- Processes a directory of video files.
- Inserts a common clip between each video.
- Re-encodes videos to a uniform format, resolution, and framerate.
- Normalizes audio levels across all clips.
- Ensures clips are taken at least 10 seconds away from the start and end of their source videos to avoid spoilers or abrupt beginnings/ends.
- Randomizes video selection.
- Supports specifying the number of videos (default is 60 for an hour-long powerhour).
- Includes a progress bar during processing for better user experience.

## Requirements

- Python 3.x
- FFmpeg

Ensure FFmpeg is installed on your system and accessible in your system's PATH.

## Usage

Execute the script from the command line, supplying the path to the video folder, the path to the common clip, the fade duration in seconds, and the desired output file name as arguments.

```bash
python powerhour_generator.py /path/to/video/folder /path/to/common_clip.mp4 fade_duration_in_seconds output_file_name.mp4
```

## Arguments

- `/path/to/video/folder`: Directory containing the video files to be processed.
- `/path/to/common_clip.mp4`: Path to the video file that will be inserted between each content video.
- `fade_duration_in_seconds`: Duration of the fade effect applied to the common clip and at the beginning and end of each video clip (in seconds).
- `output_file_name.mp4`: Filename for the output concatenated video.

## How It Works

1. The script checks the duration of each video file in the provided directory to ensure it meets the minimum duration requirement, considering additional buffers to avoid selecting clips too close to the start or end of the videos.
2. It analyzes and normalizes the audio loudness across all videos to ensure a consistent audio experience.
3. The common clip and each video file are re-encoded to the same resolution, framerate, and codecs.
4. The script then randomly selects videos (up to the specified maximum limit), processes them by inserting the common clip between each, and ensures audio levels are normalized.
5. Finally, all processed clips are concatenated into a single output file, ready to be played.

## Troubleshooting

If you run into issues with the progress bar or any other feature, verify that you're running the script in a standard terminal or command prompt environment. Some IDEs or text editors may not support the in-place line updates required for the progress bar functionality.
