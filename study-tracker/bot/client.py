from __future__ import annotations
import logging
import discord
from discord.ext import commands
from config.settings import settings
from database.db import init_db
from services.reminder_service import reminder_service
from services.live_session_service import live_session_service

logger = logging.getLogger(__name__)

INITIAL_EXTENSIONS = [
    "bot.cogs.study_cog",
    "bot.cogs.session_cog",
    "bot.cogs.notes_cog",
    "bot.cogs.leaderboard_cog",
    "bot.cogs.roast_cog",
    "bot.cogs.help_cog"
]

class StudyTrackerBot(commands.Bot):
    def __init__(self):
        # Default unprivileged intents to avoid PrivilegedIntentsRequired errors
        intents = discord.Intents.default()

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
            name="Live Sessions • /session start • /help"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        # Start Daily Inactivity Sarcastic Roast Service
        reminder_service.start(self)
        
        # Start Live Session Offline Watchdog
        live_session_service.start_watchdog(self)
