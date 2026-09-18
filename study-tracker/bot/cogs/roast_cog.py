from __future__ import annotations
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from database.db import get_db
from database.models import StudyStreak
from sqlalchemy import select
from services.roast_service import roast_service
from bot.ui.embeds import create_roast_embed

logger = logging.getLogger(__name__)

class RoastCog(commands.Cog):
    """Playful sarcastic roasting for slacking candidates."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="roast",
        description="Drop a hilarious sarcastic roast on someone who hasn't studied today!"
    )
    @app_commands.describe(user="The candidate who needs a reality check (defaults to you)")
    async def roast_candidate(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        target_user = user or interaction.user
        target_id = str(target_user.id)

        await interaction.response.defer()

        async with get_db() as db:
            streak_stmt = select(StudyStreak).where(StudyStreak.discord_id == target_id)
            streak = (await db.execute(streak_stmt)).scalar_one_or_none()
            streak_count = streak.current_streak if streak else 0

        roast_text = await roast_service.get_dynamic_roast(
            username=target_user.display_name or target_user.name,
            streak_count=streak_count
        )

        embed = create_roast_embed(roast_text, target_user.display_name or target_user.name)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(RoastCog(bot))
