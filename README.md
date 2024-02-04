# Powerhour Generator

Now you can make your own custom powerhour mixes, just give it a folder of random music videos and it will randomly extract one-minute clips from each, and stitch them together (along with fade-in and fade-out effects), with an interstitial video of your choosing.

It ensures that all videos are re-encoded to the same format, resolution, framerate, and codecs before being concatenated, so you can throw pretty much anything at it (well, anything FFmpeg can process) and it will standardize it into a nice little x264-encoded output video, for your partying pleasure.

Cheers!

## Features

- Processes a directory of video files
- Inserts a common clip between each video
- Re-encodes videos to a uniform format and resolution
- Randomizes video selection
- Supports a specified number of videos (60 by default, as that would be an hour...)
- Provides a progress bar during processing

## Requirements

- Python 3.x
- FFmpeg

Make sure you have FFmpeg installed on your system and that it's available in your system's PATH.

## Usage

Run the script from the command line providing the path to the video folder, the path to the common clip, the fade duration in seconds, and the desired output file name as arguments.

```bash
python powerhour_generator.py /path/to/video/folder /path/to/common_clip.mp4 fade_duration_in_seconds output_file_name.mp4
```

## Arguments

- `/path/to/video/folder`: The directory containing the video files to be processed.
- `/path/to/common_clip.mp4`: The path to the video file that will be inserted between each content video.
- `fade_duration_in_seconds`: The duration of the fade effect applied to the common clip (in seconds).
- `output_file_name.mp4`: The filename for the output concatenated video.

## How It Works

1. The script first checks the duration of each video file in the provided directory to ensure it meets the minimum duration requirement.
2. It then re-encodes the common clip and each video file to the same resolution, framerate, and codecs.
3. The script randomly selects videos (up to the maximum limit) and processes them, inserting the common clip between each one.
4. Finally, all processed clips are concatenated into a single output file.

## Troubleshooting

If you encounter issues with the progress bar or any other aspect of the script, ensure you are running the script in a standard terminal or command prompt. Some IDEs or text editors might not support in-place line updates required for the progress bar to function correctly.
