import os
import random
import string
from pydub import AudioSegment
from pydub.effects import speedup
import subprocess
from config import TEMP_DIR

def generate_random_id(length=8):
    """Generate random ID for temp files"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class AudioProcessor:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    def get_audio_duration(self, input_path):
        """Get audio duration"""
        try:
            audio = AudioSegment.from_file(input_path)
            return len(audio) / 1000.0  # Convert to seconds
        except:
            return 0

    def convert_audio_format(self, input_path, output_path, format_type, quality='128k'):
        """Convert audio to different format"""
        audio = AudioSegment.from_file(input_path)
        
        if format_type == 'mp3':
            audio.export(output_path, format='mp3', bitrate=quality)
        elif format_type == 'wav':
            audio.export(output_path, format='wav')
        elif format_type == 'flac':
            audio.export(output_path, format='flac')
        elif format_type == 'aac':
            audio.export(output_path, format='ipod', bitrate=quality)
        elif format_type == 'm4a':
            audio.export(output_path, format='ipod', bitrate=quality)
        elif format_type == 'ogg':
            audio.export(output_path, format='ogg', bitrate=quality)
        elif format_type == 'opus':
            audio.export(output_path, format='opus', bitrate=quality)
            
        return output_path

    def apply_slowed_reverb(self, input_path, output_path):
        """Apply slowed and reverb effect"""
        # Slow down
        audio = AudioSegment.from_file(input_path)
        slowed = speedup(audio, playback_speed=0.8)
        
        # Add reverb (simplified)
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', 'aecho=0.8:0.9:1000:0.3',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def merge_audios(self, audio_paths, output_path):
        """Merge multiple audio files"""
        combined = AudioSegment.empty()
        for path in audio_paths:
            audio = AudioSegment.from_file(path)
            combined += audio
        
        combined.export(output_path, format=output_path.split('.')[-1])
        return output_path

    def apply_8d_audio(self, input_path, output_path):
        """Apply 8D audio effect"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', 'apulsator=hz=0.08',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def equalize_audio(self, input_path, output_path, volume=0, bass=0, treble=0, speed=1.0):
        """Apply audio equalizer effects"""
        audio = AudioSegment.from_file(input_path)
        
        # Volume adjustment
        if volume != 0:
            audio = audio + volume
        
        # Speed adjustment
        if speed != 1.0:
            audio = speedup(audio, playback_speed=speed)
        
        audio.export(output_path, format=output_path.split('.')[-1])
        return output_path

    def boost_bass(self, input_path, output_path, boost_level):
        """Boost bass frequencies"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', f'bass=g={boost_level}',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def boost_treble(self, input_path, output_path, boost_level):
        """Boost treble frequencies"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', f'treble=g={boost_level}',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def trim_audio(self, input_path, output_path, start_time, end_time):
        """Trim audio from start_time to end_time"""
        audio = AudioSegment.from_file(input_path)
        trimmed = audio[start_time*1000:end_time*1000]
        trimmed.export(output_path, format=output_path.split('.')[-1])
        return output_path

    def auto_trim_audio(self, input_path, output_path, start_time, duration):
        """Auto trim audio with start time and duration"""
        audio = AudioSegment.from_file(input_path)
        trimmed = audio[start_time*1000:(start_time+duration)*1000]
        trimmed.export(output_path, format=output_path.split('.')[-1])
        return output_path

    def change_audio_speed(self, input_path, output_path, speed_percentage):
        """Change audio speed"""
        speed_factor = speed_percentage / 100.0
        cmd = [
            'ffmpeg', '-i', input_path,
            '-filter:a', f'atempo={speed_factor}',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def change_volume(self, input_path, output_path, volume_percentage):
        """Change audio volume"""
        volume_factor = volume_percentage / 100.0
        cmd = [
            'ffmpeg', '-i', input_path,
            '-filter:a', f'volume={volume_factor}',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def compress_audio(self, input_path, output_path, compression_level):
        """Compress audio file"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-acodec', 'libmp3lame',
            '-b:a', f'{compression_level}k',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path
