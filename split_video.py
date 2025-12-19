# split_video.py
# Requires ffmpeg bin installed

import os
from pathlib import Path
import subprocess

# Ensure ffmpeg bin is in PATH
ffmpeg_path = r"C:\app\ffmpeg\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]

print("PATH:", os.environ["PATH"])

# Test ffprobe
print(subprocess.run(["ffprobe", "-version"], capture_output=True, text=True).stdout)

# Import wiutils
from wiutils import convert_video_to_images

# Define source and target paths
source_folder = Path(r"C:/project/PFK/BandedRailMonitoring/soldiers_bay/CAM01-2025-11-12/video")
target_folder = Path(r"C:/project/PFK/BandedRailMonitoring/soldiers_bay/CAM01-2025-11-12/split")

# Ensure target folder exists
target_folder.mkdir(parents=True, exist_ok=True)

# Interval in seconds
interval = 1

# Loop through all MP4 files in the source folder
for file_name in os.listdir(source_folder):
    if file_name.lower().endswith(".mp4"):
        video_path = source_folder / file_name
        print(f"Processing video: {video_path}")

        # Convert video to images at specified interval
        convert_video_to_images(
            video_path=str(video_path),
            output_path=str(target_folder),
            timestamp=None,            # Optional
            image_format="jpeg",       # Options: 'jpeg' or 'png'
            offset=interval            # Interval in seconds
        )

print("✅ Video splitting completed. Images saved in:", target_folder)
