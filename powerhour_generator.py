import os
import sys
import shutil
import random
import subprocess
import json
from glob import glob
from tempfile import TemporaryDirectory
from datetime import datetime

def draw_progress_bar(progress, total, prefix='', length=50, fill='█', print_end="\r"):
    percent = "{0:.1f}".format(100 * (progress / float(total)))
    filled_length = int(length * progress // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% Complete', end=print_end)
    sys.stdout.flush()

def run_command(command, log_file_path):
    try: 
        with open(log_file_path, 'w') as log_file:
            result = subprocess.run(command, stderr=log_file, stdout=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception as e:
        with open(log_file_path, 'a') as log_file:
            log_file.write(str(datetime.now()) + " : " + str(e) + " : " + str(command))
        return False

def get_video_duration(video_file):
    try:
        duration = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                            'format=duration', '-of',
                                            'default=noprint_wrappers=1:nokey=1', video_file],
                                           text=True).strip()
        return float(duration)
    except subprocess.CalledProcessError:
        print(f"Error getting duration for {video_file}")
        return None

def analyze_loudness(video_file, log_file_path, json_output_dir):
    ffmpeg_command = [
        'ffmpeg', '-i', video_file, '-af', 'loudnorm=I=-23:LRA=7:print_format=json', '-f', 'null', '-'
    ]

    try:
        # Execute the ffmpeg command and capture the output
        output = subprocess.check_output(ffmpeg_command, stderr=subprocess.STDOUT, text=True)
        loudness_info_objects = []  # List to store all captured JSON objects
        json_data_accumulated = ""  # String to accumulate JSON data
        capturing_json = False  # Flag to indicate when to start capturing JSON data

        for line in output.splitlines():
            if '{' in line:
                capturing_json = True  # Start capturing JSON data
                json_data_accumulated = line[line.find('{'):]  # Start from '{'
            elif capturing_json:
                json_data_accumulated += line
                if '}' in line:
                    try:
                        json_obj = json.loads(json_data_accumulated)
                        loudness_info_objects.append(json_obj)  # Add the JSON object to the list
                        capturing_json = False  # Reset for the next JSON object
                        json_data_accumulated = ""  # Clear for the next accumulation
                    except json.JSONDecodeError:
                        # In case of a JSON decoding error, just reset and continue
                        capturing_json = False
                        json_data_accumulated = ""

        # Filter the captured JSON objects based on the expected keys
        expected_keys = {"input_i", "input_tp", "input_lra", "input_thresh",
                         "output_i", "output_tp", "output_lra", "output_thresh",
                         "normalization_type", "target_offset"}

        loudness_info = next((obj for obj in loudness_info_objects if set(obj.keys()) == expected_keys), None)

        if loudness_info is None:
            raise ValueError("No matching JSON loudness data found in ffmpeg output.")

        # Save the loudness information to a file
        json_file_name = os.path.basename(video_file) + '_loudness.json'
        json_file_path = os.path.join(json_output_dir, json_file_name)
        with open(json_file_path, 'w') as json_file:
            json.dump(loudness_info, json_file, indent=4)

    except subprocess.CalledProcessError as e:
        print(f"Error analyzing loudness for {video_file}. See {log_file_path}")
        with open(log_file_path, 'w') as log_file:
            log_file.write(str(e.output))
    except ValueError as e:
        print(f"Error extracting loudness data for {video_file}. See {log_file_path}")
        with open(log_file_path, 'w') as log_file:
            log_file.write(str(e))

def reencode_videos(video_file, start_time, duration, output_path, log_file_path, fade_duration, json_loudness_file):
    fade_in_start = 0
    fade_out_start = max(duration - fade_duration, 0)

    try:
        with open(json_loudness_file, 'r') as json_file:
            audio_loudness = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"There was an error loading the JSON file for {video_file}. Using default loudness values.")
        audio_loudness = {}

    audio_filters = f"loudnorm=I=-23:LRA=7:TP=-1.5:measured_I={audio_loudness.get('input_i', '-23.0')}:measured_LRA={audio_loudness.get('input_lra', '7.0')}:measured_TP={audio_loudness.get('input_tp', '-1.5')}:measured_thresh={audio_loudness.get('input_thresh', '-50.0')}:offset={audio_loudness.get('target_offset', '0.0')}:linear=true:print_format=summary"

    ffmpeg_command = [
        'ffmpeg', '-y', '-ss', str(start_time), '-t', str(duration), '-i', video_file,
        '-vf', f"scale=1280:720, fade=t=in:st={fade_in_start}:d={fade_duration}, fade=t=out:st={fade_out_start}:d={fade_duration}",
        '-af', audio_filters,
        '-r', '30', '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output_path
    ]
    return run_command(ffmpeg_command, log_file_path)

def main(video_folder, common_clip, fade_duration, output_file):
    if shutil.which('ffmpeg') is None or shutil.which('ffprobe') is None:
        print("ffmpeg or ffprobe is not installed. Please install them before running this script.")
        return

    if not os.path.isdir(video_folder) or not os.path.exists(common_clip):
        print("Specified video folder or common clip file does not exist.")
        return

    video_files = glob(os.path.join(video_folder, '*'))
    if not video_files:
        print("No video files found in the specified directory.")
        return

    with TemporaryDirectory() as temp_dir:
        ffmpeg_logs_dir = os.path.join(temp_dir, 'logs')
        loudness_json_dir = os.path.join(temp_dir, 'loudness_json')
        os.makedirs(ffmpeg_logs_dir, exist_ok=True)
        os.makedirs(loudness_json_dir, exist_ok=True)

        common_clip_log_path = os.path.join(ffmpeg_logs_dir, 'common_clip.log')
        analyze_loudness(common_clip, common_clip_log_path, loudness_json_dir)

        max_videos = 60
        video_files = random.sample(video_files, min(max_videos, len(video_files)))

        print("Analyzing loudness and checking durations...")
        loudness_results = {}
        for i, video_file in enumerate(video_files):
            duration = get_video_duration(video_file)
            if duration and duration >= 80:
                log_file_path = os.path.join(ffmpeg_logs_dir, f'loudness_{i:04d}.log')
                analyze_loudness(video_file, log_file_path, loudness_json_dir)
                loudness_results[video_file] = duration
            draw_progress_bar(i + 1, len(video_files))
        print("\nFinished analyzing loudness and checking durations.")

        common_clip_temp = os.path.join(temp_dir, 'common_clip.mp4')
        common_clip_loudness_json = os.path.join(loudness_json_dir, os.path.basename(common_clip) + '_loudness.json')

        # Make sure to analyze loudness of the common clip as well
        if not reencode_videos(common_clip, 0, fade_duration, common_clip_temp, os.path.join(ffmpeg_logs_dir, 'common_clip.log'), fade_duration, common_clip_loudness_json):
            print(f"Failed to re-encode common clip: {common_clip}")
            return

        clip_list, failed = [], 0
        for i, (video_file, duration) in enumerate(loudness_results.items(), start=1):
            start_time = random.randint(10, int(duration) - 70)
            temp_clip_name = f'temp_clip_{i:04d}.mp4'
            temp_clip_path = os.path.join(temp_dir, temp_clip_name)
            json_loudness_file = os.path.join(loudness_json_dir, os.path.basename(video_file) + '_loudness.json')

            if reencode_videos(video_file, start_time, 60, temp_clip_path, os.path.join(ffmpeg_logs_dir, f'video_{i:04d}.log'), fade_duration, json_loudness_file):
                clip_list.append(temp_clip_path)
            else:
                print(f"Failed to process video: {video_file}")
                failed += 1
            draw_progress_bar(i, len(loudness_results), prefix='Processing: ')

        print(f"\nProcessing complete. {failed} files failed to process.")

        concat_list_path = os.path.join(temp_dir, 'concat_list.txt')
        with open(concat_list_path, 'w') as concat_file:
            for i, clip_path in enumerate(clip_list):
                if i > 0:  # Add common clip before each video except the first one
                    concat_file.write(f"file '{common_clip_temp}'\n")
                concat_file.write(f"file '{clip_path}'\n")

        concat_command = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_list_path, '-c', 'copy', output_file]
        if not run_command(concat_command, os.path.join(ffmpeg_logs_dir, 'concat.log')):
            print(f"Failed to concatenate videos. See {os.path.join(ffmpeg_logs_dir, 'concat.log')}")


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python powerhour_generator.py /path/to/video/folder /path/to/common_clip.mp4 fade_duration_in_seconds output_file_name.mp4")
        sys.exit(1)

    try:
        video_folder_path = sys.argv[1]
        common_clip_path = sys.argv[2]
        fade_duration_seconds = float(sys.argv[3])
        output_file_name = sys.argv[4]
    except ValueError:
        print("Error: fade_duration_in_seconds argument must be a number.")
        sys.exit(1)
    
    main(video_folder_path, common_clip_path, fade_duration_seconds, output_file_name)
