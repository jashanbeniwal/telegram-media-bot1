from telethon import TelegramClient
from config import Config
import os

class TelethonClient:
    _instance = None
    
    def __init__(self):
        self.client = TelegramClient(
            "media_bot_session",
            Config.API_ID,
            Config.API_HASH
        )
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TelethonClient()
        return cls._instance
    
    async def start(self):
        if Config.STRING_SESSION:
            await self.client.start(session_string=Config.STRING_SESSION)
        else:
            await self.client.start(bot_token=Config.BOT_TOKEN)
    
    async def upload_large_file(self, chat_id: int, file_path: str, caption: str = "", 
                              thumb: str = None, progress_callback=None):
        """Upload large files using Telethon (for files > 2GB)"""
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
