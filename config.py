import os

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# File Size Limits (in bytes)
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB
MAX_VIDEO_DURATION = 3600  # 1 hour in seconds

# Temporary directory
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# Default Settings
DEFAULT_SETTINGS = {
    'rename_file': True,
    'upload_mode': 'video',
    'audio_quality': '128k',
    'video_quality': '720p',
    'compress_audio': False,
    'audio_speed': 100,
    'volume_level': 100
}

# Supported Formats
VIDEO_FORMATS = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm']
AUDIO_FORMATS = ['mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg', 'opus', 'wma']
DOCUMENT_FORMATS = ['txt', 'pdf', 'doc', 'docx', 'zip', 'rar', '7z', 'json', 'srt', 'vtt', 'ass', 'sbv']
