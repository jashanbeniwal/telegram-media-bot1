import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import subprocess
from config import TEMP_DIR
from .helpers import generate_random_id

class VideoProcessor:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    def compress_video(self, input_path, output_path, target_size):
        """Compress video to target size in bytes"""
        # Get video duration
        duration = self.get_video_duration(input_path)
        
        # Calculate target bitrate (in kbps)
        target_size_kb = target_size / 1024
        target_bitrate = int((target_size_kb * 8) / duration)  # kbps
        
        # Ensure minimum bitrate
        target_bitrate = max(target_bitrate, 500)  # Minimum 500 kbps
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-b:v', f'{target_bitrate}k',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def get_video_resolution(self, input_path):
        """Get video resolution"""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=s=x:p=0',
                input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return "Unknown"

    # ... rest of the existing methods remain the same ...
