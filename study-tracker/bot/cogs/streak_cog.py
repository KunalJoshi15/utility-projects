from __future__ import annotations
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from database.db import get_db
from services.topic_service import topic_service
from services.gamification_service import gamification_service
from bot.ui.embeds import (
    create_streak_detail_embed,
    create_freeze_activated_embed,
    create_leaderboard_embed
)
from bot.ui.views import StreakDashboardView, LeaderboardView

logger = logging.getLogger(__name__)

class StreakCog(commands.Cog, name="Streak"):
    """Dedicated Daily Study Streak and Habit Consistency Commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="streak",
        description="View your active daily study streak, 7-day visual consistency calendar & shields"
    )
    @app_commands.describe(user="View another candidate's study streak (optional)")
    async def view_streak(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await interaction.response.defer(ephemeral=False)
        target_user = user or interaction.user
        display_name = target_user.display_name or target_user.name

        async with get_db() as db:
            streak_details = await topic_service.get_user_streak_details(db, str(target_user.id))

        embed = create_streak_detail_embed(streak_details, display_name)
        view = StreakDashboardView(str(target_user.id), display_name) if target_user.id == interaction.user.id else None

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(
        name="freeze",
        description="Activate a streak freeze shield to protect your study streak on rest days"
    )
    async def freeze_streak(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        display_name = interaction.user.display_name or interaction.user.name

        async with get_db() as db:
            try:
                res = await topic_service.use_streak_freeze(db=db, discord_id=str(interaction.user.id))
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return
            except Exception as e:
                logger.error(f"Error activating streak freeze: {e}", exc_info=True)
                await interaction.followup.send("❌ An error occurred while activating your streak freeze.", ephemeral=True)
                return

        embed = create_freeze_activated_embed(res, display_name)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(StreakCog(bot))
