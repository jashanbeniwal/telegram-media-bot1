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

# User settings storage (in production, use a database)
user_settings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    user_id = update.effective_user.id
    if user_id not in user_settings:
        user_settings[user_id] = DEFAULT_SETTINGS.copy()
    
    welcome_text = """
🤖 **Welcome to Advanced Media Bot!**

I can process your videos, audios, documents, and URLs with advanced features:

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
• Remove forwarded tags

🔗 **URL Features:**
• Download from direct links
• Google Drive downloader
• Link shortener
• Archive extraction

⚙️ Use /settings to customize bot behavior
📥 Just send me any file or URL to get started!
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

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video files and show processing options."""
    video = update.message.video or update.message.document
    if not video:
        return
    
    file_size = video.file_size
    if file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ File size exceeds 2GB limit.")
        return
    
    # Download file
    file_id = video.file_id
    file = await context.bot.get_file(file_id)
    file_extension = video.file_name.split('.')[-1] if video.file_name else 'mp4'
    temp_file_path = f"temp/{generate_random_id()}.{file_extension}"
    
    await file.download_to_drive(temp_file_path)
    context.user_data['current_file'] = temp_file_path
    context.user_data['file_type'] = 'video'
    
    # Show video processing options
    keyboard = [
        [InlineKeyboardButton("🔇 Remove Audio & Subtitles", callback_data="video_remove_audio_subs")],
        [InlineKeyboardButton("🎵 Extract Audio & Subtitles", callback_data="video_extract_audio_subs")],
        [InlineKeyboardButton("✂️ Video Trimmer", callback_data="video_trim")],
        [InlineKeyboardButton("🔀 Video Merger", callback_data="video_merge")],
        [InlineKeyboardButton("🔇 Mute Audio", callback_data="video_mute")],
        [InlineKeyboardButton("🎵 Merge Video+Audio", callback_data="video_merge_audio")],
        [InlineKeyboardButton("📝 Merge Video+Subtitle", callback_data="video_merge_subtitle")],
        [InlineKeyboardButton("🔄 Video to GIF", callback_data="video_to_gif")],
        [InlineKeyboardButton("✂️ Video Splitter", callback_data="video_split")],
        [InlineKeyboardButton("📸 Auto Screenshots", callback_data="video_screenshots")],
        [InlineKeyboardButton("🖼️ Manual Screenshot", callback_data="video_manual_screenshot")],
        [InlineKeyboardButton("🎬 Video Sample", callback_data="video_sample")],
        [InlineKeyboardButton("🎵 Audio Converter", callback_data="video_audio_convert")],
        [InlineKeyboardButton("⚡ Video Optimizer", callback_data="video_optimize")],
        [InlineKeyboardButton("🔄 Video Converter", callback_data="video_convert")],
        [InlineKeyboardButton("📝 Rename Video", callback_data="video_rename")],
        [InlineKeyboardButton("ℹ️ Media Info", callback_data="video_info")],
        [InlineKeyboardButton("📦 Create Archive", callback_data="video_archive")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎥 **Video Processing Options**\nChoose what you want to do:",
        reply_markup=reply_markup
    )

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio files and show processing options."""
    audio = update.message.audio or update.message.document
    if not audio:
        return
    
    # Download file
    file_id = audio.file_id
    file = await context.bot.get_file(file_id)
    file_extension = audio.file_name.split('.')[-1] if audio.file_name else 'mp3'
    temp_file_path = f"temp/{generate_random_id()}.{file_extension}"
    
    await file.download_to_drive(temp_file_path)
    context.user_data['current_file'] = temp_file_path
    context.user_data['file_type'] = 'audio'
    
    # Show audio processing options
    keyboard = [
        [InlineKeyboardButton("🔄 Audio Converter", callback_data="audio_convert")],
        [InlineKeyboardButton("🌀 Slowed & Reverb", callback_data="audio_slowed_reverb")],
        [InlineKeyboardButton("🎵 Audio Merger", callback_data="audio_merge")],
        [InlineKeyboardButton("8️⃣ 8D Audio", callback_data="audio_8d")],
        [InlineKeyboardButton("🎛️ Equalizer", callback_data="audio_equalizer")],
        [InlineKeyboardButton("🔊 Bass Booster", callback_data="audio_bass")],
        [InlineKeyboardButton("🔊 Treble Booster", callback_data="audio_treble")],
        [InlineKeyboardButton("✂️ Audio Trimmer", callback_data="audio_trim")],
        [InlineKeyboardButton("⚡ Auto Trimmer", callback_data="audio_auto_trim")],
        [InlineKeyboardButton("📝 Rename Audio", callback_data="audio_rename")],
        [InlineKeyboardButton("🏷️ Tag Editor", callback_data="audio_tags")],
        [InlineKeyboardButton("🎚️ Speed Changer", callback_data="audio_speed")],
        [InlineKeyboardButton("🔊 Volume Changer", callback_data="audio_volume")],
        [InlineKeyboardButton("ℹ️ Media Info", callback_data="audio_info")],
        [InlineKeyboardButton("📦 Compress Audio", callback_data="audio_compress")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎵 **Audio Processing Options**\nChoose what you want to do:",
        reply_markup=reply_markup
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document files and show processing options."""
    document = update.message.document
    if not document:
        return
    
    # Download file
    file_id = document.file_id
    file = await context.bot.get_file(file_id)
    file_extension = document.file_name.split('.')[-1] if document.file_name else 'txt'
    temp_file_path = f"temp/{generate_random_id()}.{file_extension}"
    
    await file.download_to_drive(temp_file_path)
    context.user_data['current_file'] = temp_file_path
    context.user_data['file_type'] = 'document'
    
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
        [InlineKeyboardButton("🏷️ Remove Forwarded Tag", callback_data="doc_remove_tag")],
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📄 **Document Processing Options**\nChoose what you want to do:",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith('video_'):
        await handle_video_callback(update, context, data)
    elif data.startswith('audio_'):
        await handle_audio_callback(update, context, data)
    elif data.startswith('doc_'):
        await handle_document_callback(update, context, data)
    elif data.startswith('settings_'):
        await handle_settings_callback(update, context)

async def handle_video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle video processing callbacks."""
    query = update.callback_query
    current_file = context.user_data.get('current_file')
    
    if not current_file:
        await query.edit_message_text("❌ No file found. Please send a video file first.")
        return
    
    try:
        if data == "video_remove_audio_subs":
            output_path = f"temp/{generate_random_id()}.mp4"
            result_path = video_processor.remove_audio_subtitles(current_file, output_path)
            await send_result_file(context, query, result_path, "Video with audio and subtitles removed")
        
        elif data == "video_extract_audio_subs":
            # Extract audio
            audio_path = f"temp/{generate_random_id()}.mp3"
            audio_result = video_processor.extract_audio(current_file, audio_path)
            await context.bot.send_audio(chat_id=query.message.chat_id, audio=open(audio_result, 'rb'))
            clean_temp_files([audio_result])
            
            # Try to extract subtitles
            try:
                sub_path = f"temp/{generate_random_id()}.srt"
                sub_result = video_processor.extract_subtitles(current_file, sub_path)
                await context.bot.send_document(chat_id=query.message.chat_id, document=open(sub_result, 'rb'))
                clean_temp_files([sub_result])
            except:
                await query.edit_message_text("✅ Audio extracted! (No subtitles found in the video)")
        
        elif data == "video_mute":
            output_path = f"temp/{generate_random_id()}.mp4"
            result_path = video_processor.mute_audio(current_file, output_path)
            await send_result_file(context, query, result_path, "Video with muted audio")
        
        elif data == "video_to_gif":
            output_path = f"temp/{generate_random_id()}.gif"
            result_path = video_processor.video_to_gif(current_file, output_path)
            await send_result_file(context, query, result_path, "Video converted to GIF")
        
        # Add more video processing handlers here...
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await query.edit_message_text(f"❌ Error processing video: {str(e)}")
    finally:
        clean_temp_files([current_file])

async def handle_audio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle audio processing callbacks."""
    query = update.callback_query
    current_file = context.user_data.get('current_file')
    
    if not current_file:
        await query.edit_message_text("❌ No file found. Please send an audio file first.")
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
                [InlineKeyboardButton("OPUS", callback_data="audio_convert_opus")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("🎵 Choose output format:", reply_markup=reply_markup)
        
        elif data.startswith("audio_convert_"):
            format_type = data.split('_')[-1]
            output_path = f"temp/{generate_random_id()}.{format_type}"
            result_path = audio_processor.convert_audio_format(current_file, output_path, format_type)
            await send_result_file(context, query, result_path, f"Audio converted to {format_type.upper()}")
        
        elif data == "audio_slowed_reverb":
            output_path = f"temp/{generate_random_id()}.mp3"
            result_path = audio_processor.apply_slowed_reverb(current_file, output_path)
            await send_result_file(context, query, result_path, "Slowed & reverb audio applied")
        
        elif data == "audio_8d":
            output_path = f"temp/{generate_random_id()}.mp3"
            result_path = audio_processor.apply_8d_audio(current_file, output_path)
            await send_result_file(context, query, result_path, "8D audio effect applied")
        
        # Add more audio processing handlers here...
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        await query.edit_message_text(f"❌ Error processing audio: {str(e)}")
    finally:
        clean_temp_files([current_file])

async def handle_document_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle document processing callbacks."""
    query = update.callback_query
    current_file = context.user_data.get('current_file')
    
    if not current_file:
        await query.edit_message_text("❌ No file found. Please send a document first.")
        return
    
    try:
        if data == "doc_archive":
            output_path = f"temp/{generate_random_id()}.zip"
            result_path = file_processor.create_archive([current_file], output_path)
            await send_result_file(context, query, result_path, "Archive created")
        
        elif data == "doc_extract":
            extract_dir = f"temp/extract_{generate_random_id()}"
            os.makedirs(extract_dir, exist_ok=True)
            extracted_files = file_processor.extract_archive(current_file, extract_dir)
            
            for file_path in extracted_files:
                await context.bot.send_document(chat_id=query.message.chat_id, document=open(file_path, 'rb'))
            
            clean_temp_files(extracted_files)
            await query.edit_message_text("✅ Archive extracted successfully!")
        
        elif data == "doc_format_json":
            output_path = f"temp/{generate_random_id()}.json"
            result_path = file_processor.format_json(current_file, output_path, indent=4)
            await send_result_file(context, query, result_path, "JSON formatted")
        
        # Add more document processing handlers here...
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await query.edit_message_text(f"❌ Error processing document: {str(e)}")
    finally:
        clean_temp_files([current_file])

async def send_result_file(context, query, file_path, caption):
    """Helper function to send processed files."""
    try:
        with open(file_path, 'rb') as file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=file,
                caption=f"✅ {caption}"
            )
        await query.edit_message_text(f"✅ {caption} and sent!")
    except Exception as e:
        await query.edit_message_text(f"❌ Error sending file: {str(e)}")
    finally:
        clean_temp_files([file_path])

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred while processing your request. Please try again."
        )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
