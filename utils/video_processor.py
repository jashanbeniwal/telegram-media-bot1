import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import subprocess
from config import TEMP_DIR
from .helpers import generate_random_id

class VideoProcessor:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    def remove_audio_subtitles(self, input_path, output_path):
        """Remove audio and subtitles from video"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c', 'copy', '-an', '-sn',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def extract_audio(self, input_path, output_path):
        """Extract audio from video"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-q:a', '0', '-map', 'a',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def extract_subtitles(self, input_path, output_path):
        """Extract subtitles from video"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-map', '0:s:0', output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def trim_video(self, input_path, output_path, start_time, end_time):
        """Trim video from start_time to end_time"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c', 'copy', output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def merge_videos(self, video_paths, output_path):
        """Merge multiple videos"""
        # Create file list
        list_file = os.path.join(self.temp_dir, f"list_{generate_random_id()}.txt")
        with open(list_file, 'w') as f:
            for path in video_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
        
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file, '-c', 'copy', output_path
        ]
        subprocess.run(cmd, check=True)
        os.remove(list_file)
        return output_path

    def mute_audio(self, input_path, output_path):
        """Mute audio in video"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c', 'copy', '-an', output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def merge_video_audio(self, video_path, audio_path, output_path):
        """Merge video and audio"""
        cmd = [
            'ffmpeg', '-i', video_path, '-i', audio_path,
            '-c', 'copy', '-map', '0:v:0', '-map', '1:a:0',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def merge_video_subtitle(self, video_path, subtitle_path, output_path):
        """Merge video and subtitle"""
        cmd = [
            'ffmpeg', '-i', video_path, '-i', subtitle_path,
            '-c', 'copy', '-c:s', 'mov_text',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def video_to_gif(self, input_path, output_path, fps=10):
        """Convert video to GIF"""
        clip = VideoFileClip(input_path)
        clip.write_gif(output_path, fps=fps)
        return output_path

    def split_video(self, input_path, output_pattern, segment_duration):
        """Split video into segments"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c', 'copy', '-map', '0',
            '-segment_time', str(segment_duration),
            '-f', 'segment', output_pattern
        ]
        subprocess.run(cmd, check=True)
        return [output_pattern.replace('%03d', str(i).zfill(3)) 
                for i in range(len(os.listdir(self.temp_dir)))]

    def generate_screenshots(self, input_path, output_pattern, count=5):
        """Generate automatic screenshots"""
        duration = self.get_video_duration(input_path)
        timestamps = [duration * (i+1) / (count+1) for i in range(count)]
        
        screenshots = []
        for i, timestamp in enumerate(timestamps):
            output_path = output_pattern.replace('%d', str(i+1))
            cmd = [
                'ffmpeg', '-i', input_path,
                '-ss', str(timestamp),
                '-vframes', '1', '-q:v', '2',
                output_path
            ]
            subprocess.run(cmd, check=True)
            screenshots.append(output_path)
        
        return screenshots

    def manual_screenshot(self, input_path, output_path, timestamp):
        """Generate manual screenshot at specific timestamp"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', str(timestamp),
            '-vframes', '1', '-q:v', '2',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def generate_video_sample(self, input_path, output_path, duration=30):
        """Generate video sample"""
        total_duration = self.get_video_duration(input_path)
        start_time = random.uniform(0, max(0, total_duration - duration))
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy', output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def convert_video_format(self, input_path, output_path, format_type):
        """Convert video to different format"""
        cmd = ['ffmpeg', '-i', input_path]
        
        if format_type == 'mp4':
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        elif format_type == 'mkv':
            cmd.extend(['-c', 'copy'])
        
        cmd.append(output_path)
        subprocess.run(cmd, check=True)
        return output_path

    def get_video_duration(self, input_path):
        """Get video duration"""
        from .helpers import get_file_duration
        return get_file_duration(input_path)
