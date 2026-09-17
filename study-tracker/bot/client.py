import logging
import discord
from discord.ext import commands
from config.settings import settings
from database.db import init_db

logger = logging.getLogger(__name__)

INITIAL_EXTENSIONS = [
    "bot.cogs.study_cog",
    "bot.cogs.pomodoro_cog",
    "bot.cogs.ai_coach_cog",
    "bot.cogs.leaderboard_cog",
    "bot.cogs.help_cog"
]

class StudyTrackerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!study ",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # 1. Initialize Database
        await init_db()

        # 2. Load Cogs
        for ext in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded extension: {ext}")
            except Exception as e:
                logger.error(f"Failed to load extension {ext}: {e}", exc_info=True)

        # 3. Sync Slash Commands
        try:
            if settings.DISCORD_GUILD_ID:
                guild = discord.Object(id=int(settings.DISCORD_GUILD_ID))
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} slash commands to guild {settings.DISCORD_GUILD_ID}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} global slash commands")
        except Exception as e:
            logger.error(f"Error syncing application commands: {e}")

    async def on_ready(self):
        logger.info(f"Study Tracker Bot logged in as {self.user} (ID: {self.user.id})")
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Interview Prep • /study log • /help"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
