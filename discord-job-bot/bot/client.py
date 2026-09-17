import logging
import discord
from discord.ext import commands
from config.settings import settings
from database.db import init_db

logger = logging.getLogger(__name__)

class JobBot(commands.Bot):
    def __init__(self):
        # Default intents for slash commands
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self) -> None:
        """Called during bot initialization before connection."""
        # 1. Initialize SQLite / PostgreSQL Database
        await init_db()

        # 2. Load Cogs
        cogs = [
            "bot.cogs.jobs_cog",
            "bot.cogs.resume_cog",
            "bot.cogs.profile_cog",
            "bot.cogs.applications_cog",
            "bot.cogs.alerts_cog",
            "bot.cogs.salary_cog",
            "bot.cogs.visa_cog",
            "bot.cogs.help_cog",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded extension: {cog}")
            except Exception as e:
                logger.error(f"Failed to load extension {cog}: {e}", exc_info=True)

        # 3. Synchronize slash command tree
        try:
            if settings.DISCORD_GUILD_ID:
                guild = discord.Object(id=int(settings.DISCORD_GUILD_ID))
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} slash commands to guild ID {settings.DISCORD_GUILD_ID}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Globally synced {len(synced)} slash commands.")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        """Triggered when bot logs in to Discord Gateway."""
        logger.info(f"🎉 Bot connected as: {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} Discord servers.")
        
        # Set Activity status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="openings, alerts & resumes | /help"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_tree_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Global slash command error handling."""
        logger.error(f"Command error in {interaction.command}: {error}", exc_info=True)
        message = "An error occurred while executing this command."
        
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            message = f"⏳ Command is on cooldown. Try again in {error.retry_after:.1f} seconds."
        elif isinstance(error, discord.app_commands.MissingPermissions):
            message = "❌ You don't have the required permissions to run this command."

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

def create_bot() -> JobBot:
    bot = JobBot()
    bot.tree.on_error = bot.on_tree_error
    return bot
