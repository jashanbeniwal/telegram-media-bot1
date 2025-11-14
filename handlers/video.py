import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from utils.database import db
from utils.ffmpeg import ffmpeg_helper
from utils.helpers import helpers
from utils.buttons import buttons
from utils.progress import ProgressTracker

# Store user sessions
user_sessions = {}

@Client.on_message(filters.video | filters.document & filters.mime_type("video/mp4"))
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    await db.update_user_stats(user_id, "videos_processed")
    
    # Download video
    success, file_path = await helpers.download_file(client, message, "video")
    if not success:
        await message.reply_text("❌ Failed to download video")
        return
    
    # Store file path in user session
    user_sessions[user_id] = {"file_path": file_path, "type": "video"}
    
    # Send options menu
    await message.reply_text(
        "🎬 **Video Processing Options**\nChoose what you want to do:",
        reply_markup=buttons.get_video_buttons()
    )

@Client.on_callback_query(filters.regex("^video_"))
async def handle_video_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    # Get user session
    session = user_sessions.get(user_id)
    if not session or "file_path" not in session:
        await callback_query.answer("❌ No video found. Please send a video first.", show_alert=True)
        return
    
    input_path = session["file_path"]
    temp_dir = f"temp/{user_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    await callback_query.answer("🔄 Starting processing...")
    
    try:
        if data == "video_remove_audio":
            output_path = os.path.join(temp_dir, "no_audio.mp4")
            cmd = ffmpeg_helper.remove_audio(input_path, output_path)
            
        elif data == "video_extract_audio":
            output_path = os.path.join(temp_dir, "extracted_audio")
            cmd = ffmpeg_helper.extract_audio(input_path, output_path, "mp3")
            
        elif data == "video_trim":
            # For demo - in real implementation, ask for start/end times
            output_path = os.path.join(temp_dir, "trimmed.mp4")
            cmd = ffmpeg_helper.trim_video(input_path, output_path, "00:00:10", "00:00:30")
            
        elif data == "video_merge":
            await callback_query.message.edit_text("📤 Please send another video to merge...")
            user_sessions[user_id]["action"] = "merge_videos"
            return
            
        elif data == "video_mute":
            output_path = os.path.join(temp_dir, "muted.mp4")
            cmd = ffmpeg_helper.mute_audio(input_path, output_path)
            
        elif data == "video_to_gif":
            output_path = os.path.join(temp_dir, "converted.gif")
            cmd = ffmpeg_helper.convert_to_gif(input_path, output_path)
            
        elif data == "video_optimize":
            output_path = os.path.join(temp_dir, "optimized.mp4")
            settings = await db.get_user_settings(user_id)
            quality = settings.get("file_quality", "medium")
            cmd = ffmpeg_helper.optimize_video(input_path, output_path, quality)
            
        elif data == "video_to_audio":
            await callback_query.message.edit_text(
                "🎵 Select audio format:",
                reply_markup=buttons.get_audio_format_buttons()
            )
            user_sessions[user_id]["action"] = "video_to_audio"
            return
            
        else:
            await callback_query.answer("🚧 Feature coming soon!", show_alert=True)
            return
        
        # Execute FFmpeg command
        success = await ffmpeg_helper.run_command(cmd)
        
        if success and os.path.exists(output_path):
            # Send processed file
            if helpers.is_large_file(output_path):
                # Use Telethon for large files
                from utils.telethon_client import telethon_client
                await telethon_client.upload_large_file(
                    callback_query.message.chat.id,
                    output_path,
                    "✅ Processing complete!"
                )
            else:
                await client.send_document(
                    callback_query.message.chat.id,
                    output_path,
                    caption="✅ Processing complete!"
                )
            
            # Cleanup
            os.remove(output_path)
        else:
            await callback_query.message.edit_text("❌ Processing failed!")
            
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error: {str(e)}")
    
    # Cleanup input file after processing
    if os.path.exists(input_path):
        os.remove(input_path)

# Handle format selection for video to audio conversion
@Client.on_callback_query(filters.regex("^format_"))
async def handle_format_selection(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    format_type = data.replace("format_", "")
    
    session = user_sessions.get(user_id)
    if not session:
        await callback_query.answer("❌ Session expired", show_alert=True)
        return
    
    input_path = session["file_path"]
    temp_dir = f"temp/{user_id}"
    output_path = os.path.join(temp_dir, f"converted_audio.{format_type}")
    
    await callback_query.answer(f"🔄 Converting to {format_type.upper()}...")
    
    cmd = ffmpeg_helper.convert_audio(input_path, output_path, format_type)
    success = await ffmpeg_helper.run_command(cmd)
    
    if success and os.path.exists(output_path):
        await client.send_audio(
            callback_query.message.chat.id,
            output_path,
            caption=f"✅ Converted to {format_type.upper()}"
        )
        os.remove(output_path)
    else:
        await callback_query.message.edit_text("❌ Conversion failed!")
    
    # Cleanup
    if os.path.exists(input_path):
        os.remove(input_path)
