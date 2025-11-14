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
