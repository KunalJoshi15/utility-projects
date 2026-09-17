import asyncio
import logging
from config.settings import settings
from bot.client import StudyTrackerBot

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("study_tracker")

async def main():
    token = settings.DISCORD_BOT_TOKEN
    if not token:
        logger.error("STUDY_BOT_TOKEN / DISCORD_BOT_TOKEN is not set in environment or .env file!")
        return

    bot = StudyTrackerBot()
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Study Tracker Bot shutting down.")
