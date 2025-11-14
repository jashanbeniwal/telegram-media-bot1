from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class ButtonGenerator:
    @staticmethod
    def get_video_buttons() -> InlineKeyboardMarkup:
        """Generate video processing buttons"""
        buttons = [
            [
                InlineKeyboardButton("🔇 Remove Audio", callback_data="video_remove_audio"),
                InlineKeyboardButton("🎵 Extract Audio", callback_data="video_extract_audio")
            ],
            [
                InlineKeyboardButton("📝 Edit Caption", callback_data="video_edit_caption"),
                InlineKeyboardButton("✂️ Trim Video", callback_data="video_trim")
            ],
            [
                InlineKeyboardButton("🔀 Merge Videos", callback_data="video_merge"),
                InlineKeyboardButton("🔕 Mute Audio", callback_data="video_mute")
            ],
            [
                InlineKeyboardButton("🎵 Merge Video+Audio", callback_data="video_merge_audio"),
                InlineKeyboardButton("📜 Add Subtitles", callback_data="video_add_subtitles")
            ],
            [
                InlineKeyboardButton("🔄 Convert to GIF", callback_data="video_to_gif"),
                InlineKeyboardButton("📤 Split Video", callback_data="video_split")
            ],
            [
                InlineKeyboardButton("📸 Screenshot", callback_data="video_screenshot"),
                InlineKeyboardButton("🎞️ Manual Screenshot", callback_data="video_manual_screenshot")
            ],
            [
                InlineKeyboardButton("🎬 Create Sample", callback_data="video_sample"),
                InlineKeyboardButton("🔊 Convert to Audio", callback_data="video_to_audio")
            ],
            [
                InlineKeyboardButton("⚡ Optimize", callback_data="video_optimize"),
                InlineKeyboardButton("🔄 Convert Format", callback_data="video_convert")
            ],
            [
                InlineKeyboardButton("📝 Rename", callback_data="video_rename"),
                InlineKeyboardButton("ℹ️ Media Info", callback_data="video_info")
            ],
            [
                InlineKeyboardButton("📦 Create Archive", callback_data="video_archive"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_audio_buttons() -> InlineKeyboardMarkup:
        """Generate audio processing buttons"""
        buttons = [
            [
                InlineKeyboardButton("📝 Edit Caption", callback_data="audio_edit_caption"),
                InlineKeyboardButton("🌀 Slowed+Reverb", callback_data="audio_slow_reverb")
            ],
            [
                InlineKeyboardButton("🔄 Convert Format", callback_data="audio_convert"),
                InlineKeyboardButton("📦 Create Archive", callback_data="audio_archive")
            ],
            [
                InlineKeyboardButton("🔀 Merge Audio", callback_data="audio_merge"),
                InlineKeyboardButton("🎧 8D Audio", callback_data="audio_8d")
            ],
            [
                InlineKeyboardButton("🎛️ Equalizer", callback_data="audio_equalizer"),
                InlineKeyboardButton("🔊 Bass Boost", callback_data="audio_bass")
            ],
            [
                InlineKeyboardButton("🎶 Treble Boost", callback_data="audio_treble"),
                InlineKeyboardButton("✂️ Trim Audio", callback_data="audio_trim")
            ],
            [
                InlineKeyboardButton("⚡ Auto Trim", callback_data="audio_auto_trim"),
                InlineKeyboardButton("📝 Rename", callback_data="audio_rename")
            ],
            [
                InlineKeyboardButton("🏷️ Tag Editor", callback_data="audio_tags"),
                InlineKeyboardButton("⚡ Speed Change", callback_data="audio_speed")
            ],
            [
                InlineKeyboardButton("🔊 Volume Change", callback_data="audio_volume"),
                InlineKeyboardButton("ℹ️ Media Info", callback_data="audio_info")
            ],
            [
                InlineKeyboardButton("🗜️ Compress", callback_data="audio_compress"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_document_buttons() -> InlineKeyboardMarkup:
        """Generate document processing buttons"""
        buttons = [
            [
                InlineKeyboardButton("📝 Rename", callback_data="doc_rename"),
                InlineKeyboardButton("📦 Create Archive", callback_data="doc_archive")
            ],
            [
                InlineKeyboardButton("📤 Extract Archive", callback_data="doc_extract"),
                InlineKeyboardButton("📝 Edit Caption", callback_data="doc_edit_caption")
            ],
            [
                InlineKeyboardButton("🏷️ Remove Forward", callback_data="doc_remove_forward"),
                InlineKeyboardButton("📜 Subtitle Convert", callback_data="doc_convert_subtitle")
            ],
            [
                InlineKeyboardButton("📋 JSON Format", callback_data="doc_json_format"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_url_buttons() -> InlineKeyboardMarkup:
        """Generate URL processing buttons"""
        buttons = [
            [
                InlineKeyboardButton("📦 Extract Archive", callback_data="url_extract"),
                InlineKeyboardButton("⬇️ Download URL", callback_data="url_download")
            ],
            [
                InlineKeyboardButton("🔗 Shorten Link", callback_data="url_shorten"),
                InlineKeyboardButton("🔍 Unshorten", callback_data="url_unshorten")
            ],
            [
                InlineKeyboardButton("☁️ GDrive Download", callback_data="url_gdrive"),
                InlineKeyboardButton("📥 Bulk Download", callback_data="url_bulk")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_back_button(menu: str) -> InlineKeyboardMarkup:
        """Generate back button"""
        button = [[InlineKeyboardButton("🔙 Back", callback_data=f"back_{menu}")]]
        return InlineKeyboardMarkup(button)
    
    @staticmethod
    def get_quality_buttons() -> InlineKeyboardMarkup:
        """Generate quality selection buttons"""
        buttons = [
            [
                InlineKeyboardButton("High", callback_data="quality_high"),
                InlineKeyboardButton("Medium", callback_data="quality_medium"),
                InlineKeyboardButton("Low", callback_data="quality_low")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="back_settings")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_audio_format_buttons() -> InlineKeyboardMarkup:
        """Generate audio format selection buttons"""
        buttons = [
            [
                InlineKeyboardButton("MP3", callback_data="format_mp3"),
                InlineKeyboardButton("WAV", callback_data="format_wav"),
                InlineKeyboardButton("FLAC", callback_data="format_flac")
            ],
            [
                InlineKeyboardButton("AAC", callback_data="format_aac"),
                InlineKeyboardButton("M4A", callback_data="format_m4a"),
                InlineKeyboardButton("OPUS", callback_data="format_opus")
            ],
            [
                InlineKeyboardButton("OGG", callback_data="format_ogg"),
                InlineKeyboardButton("WMA", callback_data="format_wma"),
                InlineKeyboardButton("AC3", callback_data="format_ac3")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="back_audio")]
        ]
        return InlineKeyboardMarkup(buttons)

buttons = ButtonGenerator()
