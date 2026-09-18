from __future__ import annotations
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from database.db import get_db
from services.gamification_service import gamification_service
from bot.ui.embeds import create_leaderboard_embed
from bot.ui.views import LeaderboardView

logger = logging.getLogger(__name__)

class LeaderboardCog(commands.Cog):
    """Server study and preparation champion leaderboards."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="leaderboard",
        description="View the server study leaderboard (Topics Mastered, Active Streaks, or Study Hours)"
    )
    @app_commands.describe(
        category="Ranking category (topics, streak, or hours)"
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="📚 Top Topics Covered", value="topics"),
            app_commands.Choice(name="🔥 Longest Active Streaks", value="streak"),
            app_commands.Choice(name="⏱️ Most Dedicated Study Hours", value="hours")
        ]
    )
    async def show_leaderboard(
        self,
        interaction: discord.Interaction,
        category: Optional[app_commands.Choice[str]] = None
    ):
        await interaction.response.defer(ephemeral=False)
        selected_cat = category.value if category else "topics"

        async with get_db() as db:
            leaderboard_data = await gamification_service.get_leaderboard(db, sort_by=selected_cat)

        embed = create_leaderboard_embed(leaderboard_data, category=selected_cat)
        view = LeaderboardView(current_category=selected_cat)
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
