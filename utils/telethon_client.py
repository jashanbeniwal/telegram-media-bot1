from telethon import TelegramClient
from config import Config
import os
import logging

logger = logging.getLogger(__name__)

class TelethonClient:
    _instance = None
    
    def __init__(self):
        if Config.STRING_SESSION:
            self.client = TelegramClient(
                "media_bot_session",
                Config.API_ID,
                Config.API_HASH
            )
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("Telethon client disabled - STRING_SESSION not configured")
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TelethonClient()
        return cls._instance
    
    async def start(self):
        if self.enabled and Config.STRING_SESSION:
            await self.client.start(session_string=Config.STRING_SESSION)
            logger.info("Telethon client started successfully")
        else:
            logger.warning("Telethon client not started - STRING_SESSION not configured")
    
    async def upload_large_file(self, chat_id: int, file_path: str, caption: str = "", 
                              thumb: str = None, progress_callback=None):
        """Upload large files using Telethon (for files > 2GB)"""
        if not self.enabled:
            raise Exception("Telethon client not configured. Set STRING_SESSION environment variable.")
        
        try:
            file = await self.client.upload_file(
                file_path,
                progress_callback=progress_callback
            )
            
            # Determine file type
            if file_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                await self.client.send_file(
                    chat_id,
                    file,
                    caption=caption,
                    thumb=thumb,
                    supports_streaming=True,
                    attributes=None
                )
            elif file_path.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
                await self.client.send_file(
                    chat_id,
                    file,
                    caption=caption,
                    thumb=thumb,
                    attributes=None,
                    voice_note=False
                )
            else:
                await self.client.send_file(
                    chat_id,
                    file,
                    caption=caption
                )
        except Exception as e:
            raise e

telethon_client = TelethonClient().get_instance()
