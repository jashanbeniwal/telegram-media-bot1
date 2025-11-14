import os
import asyncio
import aiohttp
import requests
from telegram import Update
from config import MAX_DOWNLOAD_SIZE, CHUNK_SIZE, TEMP_DIR
from .helpers import generate_random_id

class LargeFileHandler:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    async def download_large_file(self, file, file_name, update: Update, context):
        """Download large files using chunked method"""
        try:
            # Get file info
            file_size = file.file_size
            
            if file_size <= MAX_DOWNLOAD_SIZE:
                # Use normal download for small files
                temp_path = f"{self.temp_dir}/{generate_random_id()}_{file_name}"
                await file.download_to_drive(temp_path)
                return temp_path
            
            # For large files, we need to use a different approach
            # Since Telegram Bot API limits to 50MB, we'll use direct file links
            # when available, or inform user to use alternative methods
            
            # Try to get file path for direct download
            file_path = file.file_path
            if not file_path:
                raise Exception("Cannot download large files directly. Please use smaller files (<50MB) or provide a direct download link.")
            
            file_url = f"https://api.telegram.org/file/bot{context.bot.token}/{file_path}"
            
            temp_path = f"{self.temp_dir}/{generate_random_id()}_{file_name}"
            
            # Send message to user about large file processing
            message = await update.message.reply_text(
                f"📥 Downloading large file ({file_size / (1024*1024):.1f}MB)... This may take a while."
            )
            
            # Download using requests with progress
            response = requests.get(file_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(temp_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress every 10%
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if progress % 20 == 0:  # Update every 20% to avoid spam
                                await message.edit_text(
                                    f"📥 Downloading... {progress:.1f}% complete"
                                )
            
            await message.edit_text("✅ File downloaded successfully!")
            return temp_path
            
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

    async def upload_large_file(self, file_path, chat_id, context, caption=""):
        """Upload large files using chunked method"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size <= 50 * 1024 * 1024:  # 50MB Telegram limit
                # Use normal upload for small files
                with open(file_path, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        caption=caption,
                        filename=os.path.basename(file_path)
                    )
                return True
            
            # For files larger than 50MB, we need to split or compress
            if file_size > 50 * 1024 * 1024:
                # Try to compress or split the file
                return await self.handle_oversize_file(file_path, chat_id, context, caption)
                
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")

    async def handle_oversize_file(self, file_path, chat_id, context, caption):
        """Handle files larger than 50MB"""
        file_size = os.path.getsize(file_path)
        
        # Check if it's a video and we can compress it
        if file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.m4v', '.webm')):
            from .video_processor import VideoProcessor
            processor = VideoProcessor()
            
            # Try to compress the video
            compressed_path = f"{self.temp_dir}/compressed_{generate_random_id()}.mp4"
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="🔄 Compressing video to fit Telegram limits..."
            )
            
            try:
                # Compress video to fit under 50MB
                target_size = 45 * 1024 * 1024  # 45MB target
                compressed_file = processor.compress_video(file_path, compressed_path, target_size)
                
                if os.path.exists(compressed_file) and os.path.getsize(compressed_file) <= 50 * 1024 * 1024:
                    with open(compressed_file, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=chat_id,
                            document=f,
                            caption=f"📹 Compressed Version\n{caption}",
                            filename=f"compressed_{os.path.basename(file_path)}"
                        )
                    await message.delete()
                    clean_temp_files([compressed_file])
                    return True
                else:
                    await message.edit_text("❌ Compression didn't reduce size enough. Trying to split file...")
            except Exception as e:
                await message.edit_text(f"❌ Compression failed: {str(e)}")
        
        # If compression fails or not applicable, split the file
        return await self.split_and_send_file(file_path, chat_id, context, caption)

    async def split_and_send_file(self, file_path, chat_id, context, caption):
        """Split large file into chunks and send"""
        try:
            file_size = os.path.getsize(file_path)
            chunk_size = 45 * 1024 * 1024  # 45MB chunks
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=f"📦 Splitting file into {total_chunks} parts..."
            )
            
            file_extension = os.path.splitext(file_path)[1]
            
            with open(file_path, 'rb') as original_file:
                for i in range(total_chunks):
                    chunk_data = original_file.read(chunk_size)
                    chunk_path = f"{self.temp_dir}/chunk_{i+1}_{generate_random_id()}{file_extension}"
                    
                    with open(chunk_path, 'wb') as chunk_file:
                        chunk_file.write(chunk_data)
                    
                    with open(chunk_path, 'rb') as chunk_file:
                        await context.bot.send_document(
                            chat_id=chat_id,
                            document=chunk_file,
                            caption=f"Part {i+1}/{total_chunks}\n{caption}",
                            filename=f"{os.path.splitext(os.path.basename(file_path))[0]}_part{i+1}{file_extension}"
                        )
                    
                    clean_temp_files([chunk_path])
                    await asyncio.sleep(1)  # Rate limiting
            
            await message.delete()
            return True
            
        except Exception as e:
            raise Exception(f"File splitting failed: {str(e)}")

    def can_download_large_file(self, file):
        """Check if we can download this large file"""
        return hasattr(file, 'file_path') and file.file_path is not None
