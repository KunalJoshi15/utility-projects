from __future__ import annotations
import logging
import discord
from discord import app_commands
from discord.ext import commands

from bot.ui.embeds import create_help_embed

logger = logging.getLogger(__name__)

class HelpCog(commands.Cog):
    """Help documentation for the Study Tracker Bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="View documentation on logging multi-topics, notes, leaderboards, and commands"
    )
    async def show_help(self, interaction: discord.Interaction):
        embed = create_help_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
