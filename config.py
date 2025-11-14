import os

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# File Size Limits (in bytes)
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024  # 50MB for direct download

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

# Chunk size for large file processing
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks
