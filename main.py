import os
import logging
import sys
from pyrogram import Client
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure temp directory exists
os.makedirs("temp", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def main():
    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create Pyrogram client
    app = Client(
        "media_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="handlers"),
        workdir=os.getcwd()
    )
    
    logger.info("Starting Media Bot...")
    
    # Start the bot
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
