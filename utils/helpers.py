import os
import random
import string
import filetype
from typing import Dict, Any
from config import TEMP_DIR

def generate_random_id(length=8):
    """Generate random ID for temp files"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_file_type(file_path):
    """Detect file type using filetype"""
    try:
        kind = filetype.guess(file_path)
        if kind is None:
            # Check extension for documents
            ext = os.path.splitext(file_path)[1].lower().replace('.', '')
            if ext in ['txt', 'pdf', 'doc', 'docx', 'zip', 'rar', '7z', 'json', 'srt', 'vtt', 'ass', 'sbv']:
                return 'document'
            return 'unknown'
        
        if kind.mime.startswith('video/'):
            return 'video'
        elif kind.mime.startswith('audio/'):
            return 'audio'
        elif kind.mime.startswith('image/'):
            return 'image'
        else:
            return 'document'
    except Exception:
        return 'unknown'

def clean_temp_files(file_paths=[]):
    """Clean temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning file {file_path}: {e}")

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names)-1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def get_file_duration(file_path):
    """Get duration of media file"""
    try:
        import subprocess
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 
            'format=duration', '-of', 
            'default=noprint_wrappers=1:nokey=1', file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)
    except:
        return 0

def is_video_file(filename):
    """Check if file is a video based on extension"""
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
    return any(filename.lower().endswith(ext) for ext in video_extensions)

def is_audio_file(filename):
    """Check if file is an audio based on extension"""
    audio_extensions = ['.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg', '.opus', '.wma', '.amr']
    return any(filename.lower().endswith(ext) for ext in audio_extensions)

def is_document_file(filename):
    """Check if file is a document based on extension"""
    doc_extensions = ['.txt', '.pdf', '.doc', '.docx', '.zip', '.rar', '.7z', '.tar', '.json', '.srt', '.vtt', '.ass', '.sbv']
    return any(filename.lower().endswith(ext) for ext in doc_extensions)
