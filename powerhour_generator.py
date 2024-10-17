def main(video_folder, common_clip, fade_duration, output_file):
    if shutil.which('ffmpeg') is None or shutil.which('ffprobe') is None:
        print("ffmpeg or ffprobe is not installed. Please install them before running this script.")
        return

    if not os.path.isdir(video_folder) or not os.path.exists(common_clip):
        print("Specified video folder or common clip file does not exist.")
        return

    excluded_extensions = ['.log', '.py']
    video_files = [f for f in glob(os.path.join(video_folder, '*')) if os.path.splitext(f)[1].lower() not in excluded_extensions]

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
            if duration and duration >= 180:  # Ensure video is at least 3 minutes long (60s start + 60s clip + 60s end)
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
            start_time = random.randint(60, int(duration) - 120)  # Start after 60s, end at least 60s before the end
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

