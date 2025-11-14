import os
import re
import aiofiles
import aiohttp
import mimetypes
from typing import Optional, Tuple
from pyrogram.types import Message

class Helpers:
    @staticmethod
    async def download_file(client, message: Message, file_type: str = "video") -> Tuple[bool, str]:
        """Download file from Telegram"""
        try:
            user_id = message.from_user.id
            temp_dir = f"temp/{user_id}"
            os.makedirs(temp_dir, exist_ok=True)
            
            if hasattr(message, file_type):
                media = getattr(message, file_type)
                file_path = await client.download_media(
                    media,
                    file_name=os.path.join(temp_dir, f"input_{user_id}")
                )
                return True, file_path
            return False, ""
        except Exception as e:
            print(f"Download error: {e}")
            return False, ""
    
    @staticmethod
    async def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        return os.path.getsize(file_path)
    
    @staticmethod
    def is_large_file(file_path: str) -> bool:
        """Check if file is larger than 2GB"""
        size = os.path.getsize(file_path)
        return size > 2 * 1024 * 1024 * 1024
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename"""
        return re.sub(r'[^\w\-_. ]', '', filename)
    
    @staticmethod
    async def detect_file_type(file_path: str) -> str:
        """Detect file type using file extension and simple mime detection"""
        import mimetypes
        
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Video extensions
        video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
        # Audio extensions  
        audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.wma', '.ogg', '.opus']
        # Image extensions
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        # Archive extensions
        archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz']
        
        if ext in video_exts:
            return 'video'
        elif ext in audio_exts:
            return 'audio'
        elif ext in image_exts:
            return 'image'
        elif ext in archive_exts:
            return 'archive'
        else:
            # Fallback to mimetype detection
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                if mime_type.startswith('video'):
                    return 'video'
                elif mime_type.startswith('audio'):
                    return 'audio'
                elif mime_type.startswith('image'):
                    return 'image'
            return 'document'
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration to HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    async def download_url(url: str, output_path: str) -> bool:
        """Download file from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        return True
            return False
        except Exception as e:
            print(f"URL download error: {e}")
            return False

helpers = Helpers()
