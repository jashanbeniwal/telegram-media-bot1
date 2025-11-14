import os
import logging
import random
import string
import asyncio
import aiohttp
import requests
import zipfile
import py7zr
import json
import filetype
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.effects import speedup

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

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Helper Functions
def generate_random_id(length=8):
    """Generate random ID for temp files"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def clean_temp_files(file_paths=[]):
    """Clean temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning file {file_path}: {e}")

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names)-1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def get_file_duration(file_path):
    """Get duration of media file"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 
            'format=duration', '-of', 
            'default=noprint_wrappers=1:nokey=1', file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)
    except:
        return 0

def is_video_file(filename):
    """Check if file is a video based on extension"""
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
    return any(filename.lower().endswith(ext) for ext in video_extensions)

def is_audio_file(filename):
    """Check if file is an audio based on extension"""
    audio_extensions = ['.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg', '.opus', '.wma', '.amr']
    return any(filename.lower().endswith(ext) for ext in audio_extensions)

def is_document_file(filename):
    """Check if file is a document based on extension"""
    doc_extensions = ['.txt', '.pdf', '.doc', '.docx', '.zip', '.rar', '.7z', '.tar', '.json', '.srt', '.vtt', '.ass', '.sbv']
    return any(filename.lower().endswith(ext) for ext in doc_extensions)

# Video Processor Class
class VideoProcessor:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    def remove_audio_subtitles(self, input_path, output_path):
        """Remove audio and subtitles from video"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c', 'copy', '-an', '-sn',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def extract_audio(self, input_path, output_path):
        """Extract audio from video"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-q:a', '0', '-map', 'a',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def mute_audio(self, input_path, output_path):
        """Mute audio in video"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c', 'copy', '-an', output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def video_to_gif(self, input_path, output_path, fps=10):
        """Convert video to GIF"""
        try:
            clip = VideoFileClip(input_path)
            clip.write_gif(output_path, fps=fps)
            return output_path
        except Exception as e:
            # Fallback to ffmpeg if moviepy fails
            cmd = [
                'ffmpeg', '-i', input_path,
                '-vf', 'fps=10,scale=320:-1:flags=lanczos',
                output_path
            ]
            subprocess.run(cmd, check=True)
            return output_path

    def convert_video_format(self, input_path, output_path, format_type):
        """Convert video to different format"""
        cmd = ['ffmpeg', '-i', input_path]
        
        if format_type == 'mp4':
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        elif format_type == 'mkv':
            cmd.extend(['-c', 'copy'])
        elif format_type == 'avi':
            cmd.extend(['-c:v', 'libx264', '-c:a', 'mp3'])
        
        cmd.append(output_path)
        subprocess.run(cmd, check=True)
        return output_path

    def get_video_duration(self, input_path):
        """Get video duration"""
        return get_file_duration(input_path)

    def compress_video(self, input_path, output_path, target_size):
        """Compress video to target size in bytes"""
        # Get video duration
        duration = self.get_video_duration(input_path)
        if duration == 0:
            duration = 60  # Default to 1 minute if cannot determine
        
        # Calculate target bitrate (in kbps)
        target_size_kb = target_size / 1024
        target_bitrate = int((target_size_kb * 8) / duration)  # kbps
        
        # Ensure minimum bitrate
        target_bitrate = max(target_bitrate, 500)  # Minimum 500 kbps
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-b:v', f'{target_bitrate}k',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def generate_screenshots(self, input_path, output_pattern, count=5):
        """Generate automatic screenshots"""
        duration = self.get_video_duration(input_path)
        if duration == 0:
            duration = 60
        
        timestamps = [duration * (i+1) / (count+1) for i in range(count)]
        
        screenshots = []
        for i, timestamp in enumerate(timestamps):
            output_path = output_pattern.replace('%d', str(i+1))
            cmd = [
                'ffmpeg', '-i', input_path,
                '-ss', str(timestamp),
                '-vframes', '1', '-q:v', '2',
                output_path
            ]
            subprocess.run(cmd, check=True)
            screenshots.append(output_path)
        
        return screenshots

# Audio Processor Class
class AudioProcessor:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    def get_audio_duration(self, input_path):
        """Get audio duration"""
        try:
            audio = AudioSegment.from_file(input_path)
            return len(audio) / 1000.0  # Convert to seconds
        except:
            return 0

    def convert_audio_format(self, input_path, output_path, format_type, quality='128k'):
        """Convert audio to different format"""
        audio = AudioSegment.from_file(input_path)
        
        if format_type == 'mp3':
            audio.export(output_path, format='mp3', bitrate=quality)
        elif format_type == 'wav':
            audio.export(output_path, format='wav')
        elif format_type == 'flac':
            audio.export(output_path, format='flac')
        elif format_type == 'aac':
            audio.export(output_path, format='ipod', bitrate=quality)
        elif format_type == 'm4a':
            audio.export(output_path, format='ipod', bitrate=quality)
        elif format_type == 'ogg':
            audio.export(output_path, format='ogg', bitrate=quality)
            
        return output_path

    def apply_slowed_reverb(self, input_path, output_path):
        """Apply slowed and reverb effect"""
        # Slow down
        audio = AudioSegment.from_file(input_path)
        slowed = speedup(audio, playback_speed=0.8)
        
        # Add reverb
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', 'aecho=0.8:0.9:1000:0.3',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def apply_8d_audio(self, input_path, output_path):
        """Apply 8D audio effect"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', 'apulsator=hz=0.08',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def change_audio_speed(self, input_path, output_path, speed_percentage):
        """Change audio speed"""
        speed_factor = speed_percentage / 100.0
        cmd = [
            'ffmpeg', '-i', input_path,
            '-filter:a', f'atempo={speed_factor}',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def change_volume(self, input_path, output_path, volume_percentage):
        """Change audio volume"""
        volume_factor = volume_percentage / 100.0
        cmd = [
            'ffmpeg', '-i', input_path,
            '-filter:a', f'volume={volume_factor}',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    def compress_audio(self, input_path, output_path, compression_level):
        """Compress audio file"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-acodec', 'libmp3lame',
            '-b:a', f'{compression_level}k',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

# File Processor Class
class FileProcessor:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    def create_archive(self, file_paths, output_path, archive_type='zip', password=None):
        """Create archive file (zip, rar, 7z)"""
        if archive_type == 'zip':
            with zipfile.ZipFile(output_path, 'w') as zipf:
                for file_path in file_paths:
                    zipf.write(file_path, os.path.basename(file_path))
                    if password:
                        zipf.setpassword(password.encode())
        
        elif archive_type == '7z':
            with py7zr.SevenZipFile(output_path, 'w', password=password) as archive:
                for file_path in file_paths:
                    archive.write(file_path, os.path.basename(file_path))
        
        return output_path

    def extract_archive(self, archive_path, output_dir, password=None):
        """Extract archive file"""
        extracted_files = []
        
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                if password:
                    zipf.setpassword(password.encode())
                zipf.extractall(output_dir)
                extracted_files = zipf.namelist()
        
        elif archive_path.endswith('.7z'):
            with py7zr.SevenZipFile(archive_path, 'r', password=password) as archive:
                archive.extractall(output_dir)
                extracted_files = archive.getnames()
        
        return [os.path.join(output_dir, f) for f in extracted_files]

    def format_json(self, input_path, output_path, indent=4):
        """Format JSON file with specified indentation"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return output_path

# Large File Handler Class
class LargeFileHandler:
    def __init__(self):
        self.temp_dir = TEMP_DIR

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
                    # Clean up compressed file
                    if os.path.exists(compressed_file):
                        os.remove(compressed_file)
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
                    
                    # Clean up chunk file
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                    await asyncio.sleep(1)  # Rate limiting
            
            await message.delete()
            return True
            
        except Exception as e:
            raise Exception(f"File splitting failed: {str(e)}")

# Initialize processors
video_processor = VideoProcessor()
audio_processor = AudioProcessor()
file_processor = FileProcessor()
large_file_handler = LargeFileHandler()

# User settings storage
user_settings = {}

# Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    user_id = update.effective_user.id
    if user_id not in user_settings:
        user_settings[user_id] = DEFAULT_SETTINGS.copy()
    
    welcome_text = """
🤖 **Welcome to Advanced Media Bot!** 🚀

I can process your videos, audios, documents up to **2GB**!

🎥 **Video Features:**
• Remove/extract audio
• Convert video formats
• Generate screenshots & GIFs
• Compress videos

🎵 **Audio Features:**
• Convert audio formats
• Apply effects (8D, slowed reverb)
• Change speed & volume
• Compress audio

📄 **Document Features:**
• Create/extract archives
• Format JSON files

⚙️ Use /settings to customize bot behavior
📥 **Send me any file to get started!**
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu."""
    user_id = update.effective_user.id
    if user_id not in user_settings:
        user_settings[user_id] = DEFAULT_SETTINGS.copy()
    
    keyboard = [
        [InlineKeyboardButton("📝 Rename File", callback_data="settings_rename")],
        [InlineKeyboardButton("📤 Upload Mode", callback_data="settings_upload")],
        [InlineKeyboardButton("🎵 Audio Quality", callback_data="settings_audio_quality")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    settings_text = "⚙️ **Bot Settings**\n\n"
    for key, value in user_settings[user_id].items():
        settings_text += f"• {key.replace('_', ' ').title()}: `{value}`\n"
    
    await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings callback queries."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "settings_rename":
        user_settings[user_id]['rename_file'] = not user_settings[user_id]['rename_file']
        await query.edit_message_text(f"✅ Rename File: {user_settings[user_id]['rename_file']}")
    
    elif data == "settings_upload":
        modes = ['video', 'document', 'file']
        current = user_settings[user_id]['upload_mode']
        next_mode = modes[(modes.index(current) + 1) % len(modes)]
        user_settings[user_id]['upload_mode'] = next_mode
        await query.edit_message_text(f"✅ Upload Mode: {next_mode}")
    
    elif data == "settings_audio_quality":
        qualities = ['64k', '128k', '192k', '256k', '320k']
        current = user_settings[user_id]['audio_quality']
        next_quality = qualities[(qualities.index(current) + 1) % len(qualities)]
        user_settings[user_id]['audio_quality'] = next_quality
        await query.edit_message_text(f"✅ Audio Quality: {next_quality}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages and detect file type."""
    message = update.message
    
    # Handle documents
    if message.document:
        await handle_document(update, context)
    
    # Handle videos
    elif message.video:
        await handle_video(update, context)
    
    # Handle audio
    elif message.audio:
        await handle_audio(update, context)
    
    # Handle text/URLs
    elif message.text and not message.text.startswith('/'):
        await handle_text(update, context)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video files and show processing options."""
    try:
        video = update.message.video or update.message.document
        if not video:
            return
        
        file_size = video.file_size
        if file_size and file_size > MAX_FILE_SIZE:
            await update.message.reply_text("❌ File size exceeds 2GB limit.")
            return
        
        # Get file name
        file_name = "video.mp4"
        if video.file_name:
            file_name = video.file_name
        elif update.message.video:
            file_name = "video.mp4"
        
        file_id = video.file_id
        file = await context.bot.get_file(file_id)
        
        # Show downloading message
        downloading_msg = await update.message.reply_text("📥 Downloading file...")
        
        # Download file
        temp_file_path = f"temp/{generate_random_id()}_{file_name}"
        await file.download_to_drive(temp_file_path)
        
        if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
            context.user_data['current_file'] = temp_file_path
            context.user_data['file_type'] = 'video'
            context.user_data['file_size'] = file_size
            
            await downloading_msg.edit_text("✅ File downloaded! Choose processing option:")
            
            # Show video processing options
            keyboard = [
                [InlineKeyboardButton("🔇 Remove Audio", callback_data="video_remove_audio")],
                [InlineKeyboardButton("🎵 Extract Audio", callback_data="video_extract_audio")],
                [InlineKeyboardButton("🔇 Mute Audio", callback_data="video_mute")],
                [InlineKeyboardButton("🔄 Video to GIF", callback_data="video_to_gif")],
                [InlineKeyboardButton("📸 Auto Screenshots", callback_data="video_screenshots")],
                [InlineKeyboardButton("🔄 Video Converter", callback_data="video_convert")],
                [InlineKeyboardButton("ℹ️ Media Info", callback_data="video_info")],
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"🎥 **Video Processing Options**\n"
                f"📁 File: {file_name}\n"
                f"💾 Size: {file_size / (1024*1024):.1f}MB\n"
                f"Choose what you want to do:",
                reply_markup=reply_markup
            )
        else:
            await downloading_msg.edit_text("❌ Failed to download the file. Please try again.")
            if os.path.exists(temp_file_path):
                clean_temp_files([temp_file_path])
    
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        await update.message.reply_text(f"❌ Error processing video file: {str(e)}")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio files and show processing options."""
    try:
        audio = update.message.audio or update.message.document
        if not audio:
            return
        
        file_size = audio.file_size
        if file_size and file_size > MAX_FILE_SIZE:
            await update.message.reply_text("❌ File size exceeds 2GB limit.")
            return
        
        # Get file name
        file_name = "audio.mp3"
        if audio.file_name:
            file_name = audio.file_name
        elif update.message.audio:
            file_name = "audio.mp3"
        
        file_id = audio.file_id
        file = await context.bot.get_file(file_id)
        
        # Show downloading message
        downloading_msg = await update.message.reply_text("📥 Downloading audio...")
        
        # Download file
        temp_file_path = f"temp/{generate_random_id()}_{file_name}"
        await file.download_to_drive(temp_file_path)
        
        if temp_file_path and os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
            context.user_data['current_file'] = temp_file_path
            context.user_data['file_type'] = 'audio'
            context.user_data['file_size'] = file_size
            
            await downloading_msg.edit_text("✅ Audio downloaded! Choose processing option:")
            
            # Show audio processing options
            keyboard = [
                [InlineKeyboardButton("🔄 Audio Converter", callback_data="audio_convert")],
                [InlineKeyboardButton("🌀 Slowed & Reverb", callback_data="audio_slowed_reverb")],
                [InlineKeyboardButton("8️⃣ 8D Audio", callback_data="audio_8d")],
                [InlineKeyboardButton("🎚️ Speed Changer", callback_data="audio_speed")],
                [InlineKeyboardButton("🔊 Volume Changer", callback_data="audio_volume")],
                [InlineKeyboardButton("ℹ️ Media Info", callback_data="audio_info")],
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"🎵 **Audio Processing Options**\n"
                f"📁 File: {file_name}\n"
                f"💾 Size: {file_size / (1024*1024):.1f}MB\n"
                f"Choose what you want to do:",
                reply_markup=reply_markup
            )
        else:
            await downloading_msg.edit_text("❌ Failed to download the audio file.")
            if os.path.exists(temp_file_path):
                clean_temp_files([temp_file_path])
    
    except Exception as e:
        logger.error(f"Error handling audio: {e}")
        await update.message.reply_text(f"❌ Error processing audio file: {str(e)}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document files and show processing options."""
    try:
        document = update.message.document
        if not document:
            return
        
        file_size = document.file_size
        if file_size and file_size > MAX_FILE_SIZE:
            await update.message.reply_text("❌ File size exceeds 2GB limit.")
            return
        
        file_name = document.file_name or "document.bin"
        file_extension = file_name.split('.')[-1] if '.' in file_name else 'bin'
        
        file_id = document.file_id
        file = await context.bot.get_file(file_id)
        
        # Show downloading message
        downloading_msg = await update.message.reply_text("📥 Downloading document...")
        
        # Download file
        temp_file_path = f"temp/{generate_random_id()}_{file_name}"
        await file.download_to_drive(temp_file_path)
        
        if temp_file_path and os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
            context.user_data['current_file'] = temp_file_path
            context.user_data['file_type'] = 'document'
            context.user_data['file_size'] = file_size
            
            await downloading_msg.edit_text("✅ Document downloaded! Choose processing option:")
            
            # Show document processing options based on file type
            keyboard = []
            
            if file_extension in ['zip', 'rar', '7z', 'tar']:
                keyboard.append([InlineKeyboardButton("📦 Extract Archive", callback_data="doc_extract")])
            
            if file_extension == 'json':
                keyboard.append([InlineKeyboardButton("📝 Format JSON", callback_data="doc_format_json")])
            
            keyboard.extend([
                [InlineKeyboardButton("📦 Create Archive", callback_data="doc_archive")],
            ])
            
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"📄 **Document Processing Options**\n"
                    f"📁 File: {file_name}\n"
                    f"💾 Size: {file_size / (1024*1024):.1f}MB\n"
                    f"Choose what you want to do:",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("ℹ️ No specific processing options available for this document type.")
        else:
            await downloading_msg.edit_text("❌ Failed to download the document.")
            if os.path.exists(temp_file_path):
                clean_temp_files([temp_file_path])
    
    except Exception as e:
        logger.error(f"Error handling document: {e}")
        await update.message.reply_text(f"❌ Error processing document file: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (URLs)."""
    text = update.message.text
    if text.startswith('http'):
        # URL detected
        keyboard = [
            [InlineKeyboardButton("📥 Download File", callback_data="url_download")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔗 **URL Detected**\nChoose what you want to do:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Send me a file (video, audio, document) to get started!")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('video_'):
        await handle_video_callback(update, context, data)
    elif data.startswith('audio_'):
        await handle_audio_callback(update, context, data)
    elif data.startswith('doc_'):
        await handle_document_callback(update, context, data)
    elif data.startswith('url_'):
        await handle_url_callback(update, context, data)
    elif data.startswith('settings_'):
        await handle_settings_callback(update, context)

async def handle_video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle video processing callbacks."""
    query = update.callback_query
    current_file = context.user_data.get('current_file')
    
    if not current_file or not os.path.exists(current_file):
        await query.edit_message_text("❌ No file found or file was deleted. Please send a video file first.")
        return
    
    try:
        if data == "video_remove_audio":
            await query.edit_message_text("🔄 Removing audio from video...")
            output_path = f"temp/{generate_random_id()}.mp4"
            result_path = video_processor.remove_audio_subtitles(current_file, output_path)
            await send_result_file(context, query, result_path, "Video with audio removed")
        
        elif data == "video_extract_audio":
            await query.edit_message_text("🔄 Extracting audio from video...")
            audio_path = f"temp/{generate_random_id()}.mp3"
            audio_result = video_processor.extract_audio(current_file, audio_path)
            await send_result_file(context, query, audio_result, "Audio extracted from video")
        
        elif data == "video_mute":
            await query.edit_message_text("🔄 Muting audio in video...")
            output_path = f"temp/{generate_random_id()}.mp4"
            result_path = video_processor.mute_audio(current_file, output_path)
            await send_result_file(context, query, result_path, "Video with muted audio")
        
        elif data == "video_to_gif":
            await query.edit_message_text("🔄 Converting video to GIF...")
            output_path = f"temp/{generate_random_id()}.gif"
            result_path = video_processor.video_to_gif(current_file, output_path)
            await send_result_file(context, query, result_path, "Video converted to GIF")
        
        elif data == "video_convert":
            # Show format options
            keyboard = [
                [InlineKeyboardButton("MP4", callback_data="video_convert_mp4")],
                [InlineKeyboardButton("MKV", callback_data="video_convert_mkv")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("🎥 Choose output format:", reply_markup=reply_markup)
        
        elif data.startswith("video_convert_"):
            format_type = data.split('_')[-1]
            await query.edit_message_text(f"🔄 Converting video to {format_type.upper()}...")
            output_path = f"temp/{generate_random_id()}.{format_type}"
            result_path = video_processor.convert_video_format(current_file, output_path, format_type)
            await send_result_file(context, query, result_path, f"Video converted to {format_type.upper()}")
        
        elif data == "video_screenshots":
            await query.edit_message_text("🔄 Generating screenshots...")
            output_pattern = f"temp/screenshot_%d_{generate_random_id()}.jpg"
            screenshots = video_processor.generate_screenshots(current_file, output_pattern, count=3)
            
            for i, screenshot in enumerate(screenshots):
                with open(screenshot, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=photo,
                        caption=f"📸 Screenshot {i+1}"
                    )
                clean_temp_files([screenshot])
            
            await query.edit_message_text("✅ Screenshots generated and sent!")
        
        elif data == "video_info":
            # Get basic file info
            file_size = os.path.getsize(current_file)
            duration = video_processor.get_video_duration(current_file)
            
            info_text = f"""
📊 **Media Information**

📁 File: `{os.path.basename(current_file)}`
💾 Size: {file_size / (1024*1024):.1f}MB
⏱️ Duration: {duration:.2f} seconds
🎬 Type: Video
            """
            await query.edit_message_text(info_text, parse_mode='Markdown')
        
        else:
            await query.edit_message_text("🔄 This feature is coming soon!")
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await query.edit_message_text(f"❌ Error processing video: {str(e)}")
    finally:
        if current_file and os.path.exists(current_file):
            clean_temp_files([current_file])

async def handle_audio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle audio processing callbacks."""
    query = update.callback_query
    current_file = context.user_data.get('current_file')
    
    if not current_file or not os.path.exists(current_file):
        await query.edit_message_text("❌ No file found or file was deleted. Please send an audio file first.")
        return
    
    try:
        if data == "audio_convert":
            # Show format options
            keyboard = [
                [InlineKeyboardButton("MP3", callback_data="audio_convert_mp3")],
                [InlineKeyboardButton("WAV", callback_data="audio_convert_wav")],
                [InlineKeyboardButton("FLAC", callback_data="audio_convert_flac")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("🎵 Choose output format:", reply_markup=reply_markup)
        
        elif data.startswith("audio_convert_"):
            format_type = data.split('_')[-1]
            await query.edit_message_text(f"🔄 Converting audio to {format_type.upper()}...")
            output_path = f"temp/{generate_random_id()}.{format_type}"
            user_id = query.from_user.id
            quality = user_settings.get(user_id, DEFAULT_SETTINGS).get('audio_quality', '128k')
            result_path = audio_processor.convert_audio_format(current_file, output_path, format_type, quality)
            await send_result_file(context, query, result_path, f"Audio converted to {format_type.upper()}")
        
        elif data == "audio_slowed_reverb":
            await query.edit_message_text("🔄 Applying slowed & reverb effect...")
            output_path = f"temp/{generate_random_id()}.mp3"
            result_path = audio_processor.apply_slowed_reverb(current_file, output_path)
            await send_result_file(context, query, result_path, "Slowed & reverb audio applied")
        
        elif data == "audio_8d":
            await query.edit_message_text("🔄 Applying 8D audio effect...")
            output_path = f"temp/{generate_random_id()}.mp3"
            result_path = audio_processor.apply_8d_audio(current_file, output_path)
            await send_result_file(context, query, result_path, "8D audio effect applied")
        
        elif data == "audio_info":
            # Get basic file info
            file_size = os.path.getsize(current_file)
            duration = audio_processor.get_audio_duration(current_file)
            
            info_text = f"""
📊 **Media Information**

📁 File: `{os.path.basename(current_file)}`
💾 Size: {file_size / (1024*1024):.1f}MB
⏱️ Duration: {duration:.2f} seconds
🎵 Type: Audio
            """
            await query.edit_message_text(info_text, parse_mode='Markdown')
        
        else:
            await query.edit_message_text("🔄 This feature is coming soon!")
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        await query.edit_message_text(f"❌ Error processing audio: {str(e)}")
    finally:
        if current_file and os.path.exists(current_file):
            clean_temp_files([current_file])

async def handle_document_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle document processing callbacks."""
    query = update.callback_query
    current_file = context.user_data.get('current_file')
    
    if not current_file or not os.path.exists(current_file):
        await query.edit_message_text("❌ No file found or file was deleted. Please send a document first.")
        return
    
    try:
        if data == "doc_archive":
            await query.edit_message_text("🔄 Creating archive...")
            output_path = f"temp/{generate_random_id()}.zip"
            result_path = file_processor.create_archive([current_file], output_path)
            await send_result_file(context, query, result_path, "Archive created")
        
        elif data == "doc_extract":
            await query.edit_message_text("🔄 Extracting archive...")
            extract_dir = f"temp/extract_{generate_random_id()}"
            os.makedirs(extract_dir, exist_ok=True)
            extracted_files = file_processor.extract_archive(current_file, extract_dir)
            
            for file_path in extracted_files:
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as doc:
                        await context.bot.send_document(
                            chat_id=query.message.chat_id, 
                            document=doc,
                            filename=os.path.basename(file_path)
                        )
            
            # Clean up extracted files
            for file_path in extracted_files:
                if os.path.exists(file_path):
                    clean_temp_files([file_path])
            await query.edit_message_text("✅ Archive extracted successfully!")
        
        elif data == "doc_format_json":
            await query.edit_message_text("🔄 Formatting JSON...")
            output_path = f"temp/{generate_random_id()}.json"
            result_path = file_processor.format_json(current_file, output_path, indent=4)
            await send_result_file(context, query, result_path, "JSON formatted")
        
        else:
            await query.edit_message_text("🔄 This feature is coming soon!")
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await query.edit_message_text(f"❌ Error processing document: {str(e)}")
    finally:
        if current_file and os.path.exists(current_file):
            clean_temp_files([current_file])

async def handle_url_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle URL processing callbacks."""
    query = update.callback_query
    await query.edit_message_text("🔗 URL processing feature will be implemented soon!")

async def send_result_file(context, query, file_path, caption):
    """Helper function to send processed files."""
    try:
        chat_id = query.message.chat_id
        
        # Check file size
        file_size = os.path.getsize(file_path)
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            # Use large file handler for files > 50MB
            success = await large_file_handler.upload_large_file(
                file_path, chat_id, context, f"✅ {caption}"
            )
        else:
            # Use normal upload for small files
            with open(file_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    caption=f"✅ {caption}",
                    filename=os.path.basename(file_path)
                )
            success = True
        
        if success:
            await query.edit_message_text(f"✅ {caption} and sent!")
        else:
            await query.edit_message_text(f"✅ {caption} but upload failed.")
            
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await query.edit_message_text(f"❌ Error sending file: {str(e)}")
    finally:
        clean_temp_files([file_path])

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and update.effective_user:
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="❌ An error occurred while processing your request. Please try again."
            )
        except:
            pass

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    print("🤖 Bot is running with 2GB file support...")
    application.run_polling()

if __name__ == '__main__':
    main()
