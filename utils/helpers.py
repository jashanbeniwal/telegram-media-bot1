import os
import random
import string
from typing import Dict, Any
import magic
from config import TEMP_DIR

def generate_random_id(length=8):
    """Generate random ID for temp files"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_file_type(file_path):
    """Detect file type using python-magic"""
    mime = magic.Magic(mime=True)
    file_mime = mime.from_file(file_path)
    
    if file_mime.startswith('video/'):
        return 'video'
    elif file_mime.startswith('audio/'):
        return 'audio'
    elif file_mime.startswith('image/'):
        return 'image'
    else:
        return 'document'

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
