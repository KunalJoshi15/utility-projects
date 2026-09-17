import os
import sys
import asyncio
import logging
from config.settings import settings
from bot.client import create_bot

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger("main")

async def main():
    logger.info("Starting Discord Job Search & Easy Apply Bot...")

    if not settings.DISCORD_BOT_TOKEN:
        logger.warning(
            "DISCORD_BOT_TOKEN is not set in environment or .env file! "
            "Please create your .env file with your Discord Bot token before starting."
        )

    bot = create_bot()
    
    try:
        if settings.DISCORD_BOT_TOKEN:
            await bot.start(settings.DISCORD_BOT_TOKEN)
        else:
            logger.info("Dry-run / test initialization mode...")
            await bot.setup_hook()
            logger.info("Bot hooks and database initialized successfully.")
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Bot shutdown requested.")
    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}", exc_info=True)
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
