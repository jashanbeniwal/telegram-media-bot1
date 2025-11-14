import asyncio
import os
import json
from typing import List, Dict, Any
import ffmpeg

class FFmpegHelper:
    @staticmethod
    async def run_command(cmd: List[str]) -> bool:
        """Run FFmpeg command asynchronously"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"FFmpeg error: {stderr.decode()}")
            return False
        return True
    
    @staticmethod
    def remove_audio(input_path: str, output_path: str) -> List[str]:
        """Remove audio from video"""
        return [
            'ffmpeg', '-i', input_path,
            '-c', 'copy', '-an',
            output_path
        ]
    
    @staticmethod
    def extract_audio(input_path: str, output_path: str, format: str = 'mp3') -> List[str]:
        """Extract audio from video"""
        return [
            'ffmpeg', '-i', input_path,
            '-q:a', '0', '-map', 'a',
            f'{output_path}.{format}'
        ]
    
    @staticmethod
    def extract_subtitles(input_path: str, output_path: str) -> List[str]:
        """Extract subtitles from video"""
        return [
            'ffmpeg', '-i', input_path,
            '-map', '0:s:0', f'{output_path}.srt'
        ]
    
    @staticmethod
    def trim_video(input_path: str, output_path: str, start: str, end: str) -> List[str]:
        """Trim video from start to end time"""
        return [
            'ffmpeg', '-i', input_path,
            '-ss', start, '-to', end,
            '-c', 'copy', output_path
        ]
    
    @staticmethod
    def merge_videos(input_files: List[str], output_path: str) -> List[str]:
        """Merge multiple videos"""
        # Create file list
        list_file = f"{output_path}_list.txt"
        with open(list_file, 'w') as f:
            for file in input_files:
                f.write(f"file '{file}'\n")
        
        return [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file, '-c', 'copy', output_path
        ]
    
    @staticmethod
    def mute_audio(input_path: str, output_path: str) -> List[str]:
        """Mute audio in video"""
        return [
            'ffmpeg', '-i', input_path,
            '-an', '-c:v', 'copy', output_path
        ]
    
    @staticmethod
    def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> List[str]:
        """Merge video with external audio"""
        return [
            'ffmpeg', '-i', video_path, '-i', audio_path,
            '-c', 'copy', '-map', '0:v:0', '-map', '1:a:0',
            output_path
        ]
    
    @staticmethod
    def add_subtitles(input_path: str, subtitle_path: str, output_path: str) -> List[str]:
        """Add subtitles to video"""
        return [
            'ffmpeg', '-i', input_path, '-i', subtitle_path,
            '-c', 'copy', '-c:s', 'mov_text',
            '-metadata:s:s:0', 'language=eng',
            output_path
        ]
    
    @staticmethod
    def convert_to_gif(input_path: str, output_path: str, fps: int = 10) -> List[str]:
        """Convert video to GIF"""
        return [
            'ffmpeg', '-i', input_path,
            '-vf', f'fps={fps},scale=320:-1:flags=lanczos',
            '-c:v', 'gif', output_path
        ]
    
    @staticmethod
    def split_video(input_path: str, output_pattern: str, segment_time: int) -> List[str]:
        """Split video into segments"""
        return [
            'ffmpeg', '-i', input_path,
            '-c', 'copy', '-map', '0',
            '-segment_time', str(segment_time),
            '-f', 'segment', output_pattern
        ]
    
    @staticmethod
    def take_screenshot(input_path: str, output_path: str, time: str) -> List[str]:
        """Take screenshot at specific time"""
        return [
            'ffmpeg', '-i', input_path,
            '-ss', time, '-vframes', '1',
            '-q:v', '2', output_path
        ]
    
    @staticmethod
    def convert_audio(input_path: str, output_path: str, format: str) -> List[str]:
        """Convert audio to different format"""
        codec_map = {
            'mp3': 'libmp3lame',
            'wav': 'pcm_s16le',
            'flac': 'flac',
            'aac': 'aac',
            'm4a': 'aac',
            'opus': 'libopus',
            'ogg': 'libvorbis'
        }
        
        return [
            'ffmpeg', '-i', input_path,
            '-c:a', codec_map.get(format, 'libmp3lame'),
            output_path
        ]
    
    @staticmethod
    def optimize_video(input_path: str, output_path: str, quality: str = "medium") -> List[str]:
        """Optimize video size and quality"""
        quality_presets = {
            "high": ["-crf", "23"],
            "medium": ["-crf", "28"],
            "low": ["-crf", "32"]
        }
        
        cmd = ['ffmpeg', '-i', input_path]
        cmd.extend(quality_presets.get(quality, ["-crf", "28"]))
        cmd.extend(['-c:v', 'libx264', '-preset', 'medium', output_path])
        return cmd
    
    @staticmethod
    def change_audio_speed(input_path: str, output_path: str, speed: float) -> List[str]:
        """Change audio speed"""
        return [
            'ffmpeg', '-i', input_path,
            '-filter:a', f'atempo={speed}',
            '-vn', output_path
        ]
    
    @staticmethod
    def change_volume(input_path: str, output_path: str, volume: float) -> List[str]:
        """Change audio volume"""
        return [
            'ffmpeg', '-i', input_path,
            '-filter:a', f'volume={volume}',
            output_path
        ]
    
    @staticmethod
    def apply_bass_boost(input_path: str, output_path: str, level: int) -> List[str]:
        """Apply bass boost to audio"""
        return [
            'ffmpeg', '-i', input_path,
            '-af', f'bass=g={level}',
            output_path
        ]
    
    @staticmethod
    def apply_treble_boost(input_path: str, output_path: str, level: int) -> List[str]:
        """Apply treble boost to audio"""
        return [
            'ffmpeg', '-i', input_path,
            '-af', f'treble=g={level}',
            output_path
        ]
    
    @staticmethod
    def create_8d_audio(input_path: str, output_path: str) -> List[str]:
        """Create 8D audio effect"""
        return [
            'ffmpeg', '-i', input_path,
            '-af', 'apulsator=hz=0.08',
            output_path
        ]
    
    @staticmethod
    def apply_slow_reverb(input_path: str, output_path: str) -> List[str]:
        """Apply slowed + reverb effect"""
        return [
            'ffmpeg', '-i', input_path,
            '-af', 'atempo=0.8,aecho=1.0:0.7:20:0.5',
            output_path
        ]
    
    @staticmethod
    def get_media_info(input_path: str) -> Dict[str, Any]:
        """Get media information using ffprobe"""
        try:
            probe = ffmpeg.probe(input_path)
            return probe
        except Exception as e:
            return {"error": str(e)}

ffmpeg_helper = FFmpegHelper()
