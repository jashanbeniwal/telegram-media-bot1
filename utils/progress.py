import asyncio
from pyrogram.types import Message
from typing import Callable

class ProgressTracker:
    def __init__(self, client, chat_id: int, message_id: int, total: int):
        self.client = client
        self.chat_id = chat_id
        self.message_id = message_id
        self.total = total
        self.current = 0
        self.last_update = 0
    
    async def update(self, current: int):
        """Update progress bar"""
        self.current = current
        percentage = (current / self.total) * 100
        
        # Only update every 5% to avoid spam
        if percentage - self.last_update >= 5:
            progress_bar = self._create_progress_bar(percentage)
            text = f"🔄 Processing...\n{progress_bar} {percentage:.1f}%"
            
            try:
                await self.client.edit_message_text(
                    self.chat_id,
                    self.message_id,
                    text
                )
                self.last_update = percentage
            except Exception:
                pass
    
    def _create_progress_bar(self, percentage: float, length: int = 20) -> str:
        """Create visual progress bar"""
        filled = int(length * percentage / 100)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"

async def track_progress(current, total, progress_tracker: ProgressTracker):
    """Track upload/download progress"""
    await progress_tracker.update(current)

def create_progress_callback(progress_tracker: ProgressTracker) -> Callable:
    """Create progress callback function"""
    async def callback(current, total):
        await track_progress(current, total, progress_tracker)
    return callback
