import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from config import BOT_TOKEN, DEFAULT_SETTINGS, MAX_FILE_SIZE
from utils.video_processor import VideoProcessor
from utils.audio_processor import AudioProcessor
from utils.file_processor import FileProcessor
from utils.large_file_handler import LargeFileHandler
from utils.helpers import generate_random_id, clean_temp_files, get_file_type

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize processors
video_processor = VideoProcessor()
audio_processor = AudioProcessor()
file_processor = FileProcessor()
large_file_handler = LargeFileHandler()

# User settings storage
user_settings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    user_id = update.effective_user.id
    if user_id not in user_settings:
        user_settings[user_id] = DEFAULT_SETTINGS.copy()
    
    welcome_text = """
🤖 **Welcome to Advanced Media Bot!** 🚀

I can process your videos, audios, documents up to **2GB**!

🎥 **Video Features:**
• Remove/extract audio & subtitles
• Trim, merge, convert videos  
• Generate screenshots & GIFs
• Optimize and rename videos

🎵 **Audio Features:**
• Convert formats with custom quality
• Apply effects (8D, slowed reverb)
• Boost bass/treble, change speed
• Trim, merge, compress audio

📄 **Document Features:**
• Create/extract archives
• Convert subtitles
• Format JSON files

🔗 **URL Features:**
• Download from direct links
• Google Drive downloader
• Link shortener
• Archive extraction

⚙️ Use /settings to customize bot behavior
📥 **Send me any file (up to 2GB) to get started!**
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
        [InlineKeyboardButton("🎥 Video Quality", callback_data="settings_video_quality")],
        [InlineKeyboardButton("🔊 Audio Speed", callback_data="settings_audio_speed")],
        [InlineKeyboardButton("🔊 Volume Level", callback_data="settings_volume")],
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
        
        # Download file using large file handler
        temp_file_path = await large_file_handler.download_large_file(
            file, file_name, update, context
        )
        
        if temp_file_path and os.path.exists(temp_file_path):
            context.user_data['current_file'] = temp_file_path
            context.user_data['file_type'] = 'video'
            context.user_data['file_size'] = file_size
            
            # Show video processing options
            keyboard = [
                [InlineKeyboardButton("🔇 Remove Audio", callback_data="video_remove_audio")],
                [InlineKeyboardButton("🎵 Extract Audio", callback_data="video_extract_audio")],
                [InlineKeyboardButton("🔇 Mute Audio", callback_data="video_mute")],
                [InlineKeyboardButton("🔄 Video to GIF", callback_data="video_to_gif")],
                [InlineKeyboardButton("📸 Auto Screenshots", callback_data="video_screenshots")],
                [InlineKeyboardButton("🎬 Video Sample", callback_data="video_sample")],
                [InlineKeyboardButton("🎵 Audio Converter", callback_data="video_audio_convert")],
                [InlineKeyboardButton("🔄 Video Converter", callback_data="video_convert")],
                [InlineKeyboardButton("⚡ Compress Video", callback_data="video_compress")],
                [InlineKeyboardButton("📝 Rename Video", callback_data="video_rename")],
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
            await update.message.reply_text("❌ Failed to download the file. Please try again.")
    
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
        
        # Download file using large file handler
        temp_file_path = await large_file_handler.download_large_file(
            file, file_name, update, context
        )
        
        if temp_file_path and os.path.exists(temp_file_path):
            context.user_data['current_file'] = temp_file_path
            context.user_data['file_type'] = 'audio'
            context.user_data['file_size'] = file_size
            
            # Show audio processing options
            keyboard = [
                [InlineKeyboardButton("🔄 Audio Converter", callback_data="audio_convert")],
                [InlineKeyboardButton("🌀 Slowed & Reverb", callback_data="audio_slowed_reverb")],
                [InlineKeyboardButton("8️⃣ 8D Audio", callback_data="audio_8d")],
                [InlineKeyboardButton("🎛️ Equalizer", callback_data="audio_equalizer")],
                [InlineKeyboardButton("🔊 Bass Booster", callback_data="audio_bass")],
                [InlineKeyboardButton("✂️ Audio Trimmer", callback_data="audio_trim")],
                [InlineKeyboardButton("🎚️ Speed Changer", callback_data="audio_speed")],
                [InlineKeyboardButton("🔊 Volume Changer", callback_data="audio_volume")],
                [InlineKeyboardButton("📦 Compress Audio", callback_data="audio_compress")],
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
            await update.message.reply_text("❌ Failed to download the audio file.")
    
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
        
        # Download file using large file handler
        temp_file_path = await large_file_handler.download_large_file(
            file, file_name, update, context
        )
        
        if temp_file_path and os.path.exists(temp_file_path):
            context.user_data['current_file'] = temp_file_path
            context.user_data['file_type'] = 'document'
            context.user_data['file_size'] = file_size
            
            # Show document processing options based on file type
            keyboard = []
            
            if file_extension in ['zip', 'rar', '7z', 'tar']:
                keyboard.append([InlineKeyboardButton("📦 Extract Archive", callback_data="doc_extract")])
            
            if file_extension in ['srt', 'vtt', 'ass', 'sbv']:
                keyboard.append([InlineKeyboardButton("🔄 Convert Subtitle", callback_data="doc_convert_sub")])
            
            if file_extension == 'json':
                keyboard.append([InlineKeyboardButton("📝 Format JSON", callback_data="doc_format_json")])
            
            keyboard.extend([
                [InlineKeyboardButton("📝 Rename File", callback_data="doc_rename")],
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
            await update.message.reply_text("❌ Failed to download the document.")
    
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
            [InlineKeyboardButton("🔗 Shorten URL", callback_data="url_shorten")],
            [InlineKeyboardButton("📦 Extract Archive", callback_data="url_extract")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔗 **URL Detected**\nChoose what you want to do:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Send me a file (video, audio, document up to 2GB) or a URL to get started!")

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
        
        elif data == "video_compress":
            await query.edit_message_text("🔄 Compressing video...")
            output_path = f"temp/compressed_{generate_random_id()}.mp4"
            file_size = context.user_data.get('file_size', 0)
            target_size = min(45 * 1024 * 1024, file_size // 2)  # Target 45MB or half original
            result_path = video_processor.compress_video(current_file, output_path, target_size)
            await send_result_file(context, query, result_path, "Video compressed")
        
        elif data == "video_convert":
            # Show format options
            keyboard = [
                [InlineKeyboardButton("MP4", callback_data="video_convert_mp4")],
                [InlineKeyboardButton("MKV", callback_data="video_convert_mkv")],
                [InlineKeyboardButton("AVI", callback_data="video_convert_avi")],
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
💾 Size: {file_size / (1024*1024*1024):.2f}GB
⏱️ Duration: {duration:.2f} seconds
🎬 Type: Video
📊 Resolution: {video_processor.get_video_resolution(current_file)}
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
                [InlineKeyboardButton("AAC", callback_data="audio_convert_aac")],
                [InlineKeyboardButton("M4A", callback_data="audio_convert_m4a")],
                [InlineKeyboardButton("OGG", callback_data="audio_convert_ogg")],
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
        
        elif data == "audio_compress":
            await query.edit_message_text("🔄 Compressing audio...")
            output_path = f"temp/compressed_{generate_random_id()}.mp3"
            result_path = audio_processor.compress_audio(current_file, output_path, 128)
            await send_result_file(context, query, result_path, "Audio compressed")
        
        elif data == "audio_info":
            # Get basic file info
            file_size = os.path.getsize(current_file)
            duration = audio_processor.get_audio_duration(current_file)
            
            info_text = f"""
📊 **Media Information**

📁 File: `{os.path.basename(current_file)}`
💾 Size: {file_size / (1024*1024*1024):.2f}GB
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
                    await large_file_handler.upload_large_file(
                        file_path, query.message.chat_id, context, 
                        f"Extracted: {os.path.basename(file_path)}"
                    )
            
            clean_temp_files(extracted_files)
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
        
        # Use large file handler for upload
        success = await large_file_handler.upload_large_file(
            file_path, chat_id, context, f"✅ {caption}"
        )
        
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
