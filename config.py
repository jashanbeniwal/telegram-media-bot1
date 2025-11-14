import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    
    # Telethon String Session (for large file uploads)
    STRING_SESSION = os.getenv("STRING_SESSION")
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "telegram_media_bot")
    
    # Temporary Directory
    TEMP_DIR = os.getenv("TEMP_DIR", "temp")
    
    # Maximum File Size (in bytes)
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    
    # Admin User IDs
    ADMINS = list(map(int, os.getenv("ADMINS", "").split())) if os.getenv("ADMINS") else []
    
    # Thumbnail Configuration
    THUMBNAIL_SIZE = (320, 320)
    
    # Queue Configuration
    MAX_CONCURRENT_JOBS = 3
    
    @classmethod
    def validate(cls):
        required_vars = ["BOT_TOKEN", "API_ID", "API_HASH", "STRING_SESSION", "MONGODB_URI"]
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
