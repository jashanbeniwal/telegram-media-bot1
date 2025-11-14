from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import db
from utils.buttons import buttons

@Client.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    # Ensure user exists in database
    user = await db.get_user(user_id)
    if not user:
        await db.create_user(user_id, username)
    
    welcome_text = """
🎬 **Welcome to Advanced Media Bot!**

I can process your videos, audio, documents, and URLs with **69+ advanced features**:

✅ **Video Processing**: Trim, merge, convert, optimize, etc.
✅ **Audio Tools**: Convert, edit, effects, equalizer, etc.  
✅ **Document Tools**: Archive, rename, subtitle convert, etc.
✅ **URL Processing**: Download, shorten, GDrive, etc.
✅ **Bulk Operations**: Process multiple files at once

**📚 How to use:**
1. Send me a video/audio/document/URL
2. Choose from the menu options
3. Wait for processing
4. Download your file!

Use /settings to customize your preferences.
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📚 Help", callback_data="help"),
         InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

@Client.on_message(filters.command("help"))
async def help_command(client, message: Message):
    help_text = """
**📖 Bot Help Guide**

**Video Features:**
• Remove/Extract Audio & Subtitles
• Trim, Merge, Convert formats  
• Optimize, Rename, Create GIF
• Screenshots, Samples, Archives

**Audio Features:**
• Convert between 10+ formats
• Slowed+Reverb, 8D Audio effects
• Bass/Treble boost, Equalizer
• Trim, Speed/Volume change
• Tag editor, Compressor

**Document Features:**
• Archive create/extract (zip/rar/7z)
• Subtitle conversion (srt/vtt/ass)
• JSON formatting
• Forward tag removal

**URL Features:**
• Download from 1000+ sites (yt-dlp)
• Google Drive support
• Link shortener/unshortener
• Bulk URL downloader

**Bulk Mode:**
Process multiple files with one command!

**Need help?** Contact @admin
    """
    
    await message.reply_text(help_text)

@Client.on_message(filters.command("stats"))
async def stats_command(client, message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if user:
        stats = user.get("usage_stats", {})
        stats_text = f"""
**📊 Your Usage Statistics**

🎬 Videos Processed: `{stats.get('videos_processed', 0)}`
🎵 Audio Processed: `{stats.get('audios_processed', 0)}`
📄 Documents Processed: `{stats.get('documents_processed', 0)}`
🔗 URLs Processed: `{stats.get('urls_processed', 0)}`

**Account Status:** {'⭐ Premium' if user.get('premium') else '🆓 Free'}
        """
        await message.reply_text(stats_text)
