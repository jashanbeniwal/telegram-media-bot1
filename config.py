import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", "25331263"))
    API_HASH = os.getenv("API_HASH", "cab85305bf85125a2ac053210bcd1030")
    
    # Telethon String Session (for large file uploads)
    STRING_SESSION = os.getenv("STRING_SESSION")
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://rs92573993688:pVf4EeDuRi2o92ex@cluster0.9u29q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "rs92573993688")
    
    # Temporary Directory
    TEMP_DIR = os.getenv("TEMP_DIR", "temp")
    
    # Maximum File Size (in bytes)
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    
    # Admin User IDs
    ADMINS = list(map(int, os.getenv("ADMINS", "1955406483").split())) if os.getenv("ADMINS") else []
    
 # Thumbnail Configuration
    THUMBNAIL_SIZE = (320, 320)
    
    # Queue Configuration
    MAX_CONCURRENT_JOBS = 3
    
    @classmethod
    def validate(cls):
        required_vars = ["BOT_TOKEN", "API_ID", "API_HASH", "MONGODB_URI"]
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Warn about missing STRING_SESSION but don't fail
        if not cls.STRING_SESSION:
            print("⚠️  WARNING: STRING_SESSION not set. Large file uploads (>2GB) will be disabled.")
