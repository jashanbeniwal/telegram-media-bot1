import os
import logging
import sys
import asyncio
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

async def main_async():
    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Create Pyrogram client
    app = Client(
        "media_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="handlers")
    )
    
    logger.info("Starting Media Bot...")
    
    # Start health server in background if needed
    # await start_health_server()
    
    await app.start()
    logger.info("Bot started successfully!")
    
    # Keep running
    await asyncio.Event().wait()

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
