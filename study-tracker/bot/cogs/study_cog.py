from __future__ import annotations
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from database.db import get_db
from services.topic_service import topic_service
from bot.ui.embeds import (
    create_study_logged_embed,
    create_profile_embed
)
from bot.ui.modals import QuickLogModal

logger = logging.getLogger(__name__)

class StudyCog(commands.GroupCog, group_name="study"):
    """Core daily study logging and profile commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="log",
        description="Log your daily study session. Supports 1 or multiple numbered topics!"
    )
    @app_commands.describe(
        topics="Topics studied (e.g. '1. Factory Pattern 2. 0/1 Knapsack 3. Redis Caching')",
        notes="Key takeaways, learnings, or revision notes (optional)",
        duration="Total study minutes (default: 45)",
        problems="Number of coding problems / design questions solved (default: 0)",
        category="Domain (e.g. DSA, LLD, HLD, Cloud, General)"
    )
    async def log_study(
        self,
        interaction: discord.Interaction,
        topics: str,
        notes: Optional[str] = None,
        duration: Optional[int] = 45,
        problems: Optional[int] = 0,
        category: Optional[str] = "General"
    ):
        await interaction.response.defer(ephemeral=False)

        async with get_db() as db:
            try:
                result = await topic_service.log_study_activity(
                    db=db,
                    discord_id=str(interaction.user.id),
                    raw_topics=topics,
                    notes=notes,
                    duration_minutes=duration or 45,
                    problems_solved=problems or 0,
                    category=category or "General",
                    username=interaction.user.name,
                    display_name=interaction.user.display_name
                )
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return
            except Exception as e:
                logger.error(f"Error in /study log: {e}", exc_info=True)
                await interaction.followup.send("❌ An error occurred while recording your study session.", ephemeral=True)
                return

        embed = create_study_logged_embed(result, interaction.user.display_name or interaction.user.name)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="quicklog",
        description="Open an interactive popup modal to easily enter multiple topics and notes"
    )
    async def quicklog(self, interaction: discord.Interaction):
        modal = QuickLogModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="profile",
        description="View your candidate rank, badges, study hours, and preparation scorecard"
    )
    @app_commands.describe(user="View another candidate's study scorecard (optional)")
    async def view_profile(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await interaction.response.defer(ephemeral=False)
        target_user = user or interaction.user

        async with get_db() as db:
            summary = await topic_service.get_user_profile_summary(db, str(target_user.id))

        embed = create_profile_embed(summary, target_user.display_name or target_user.name)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="streak",
        description="View your active daily study streak and consistency stats"
    )
    async def view_streak(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        async with get_db() as db:
            summary = await topic_service.get_user_profile_summary(db, str(interaction.user.id))

        streak = summary["streak"]
        longest = summary["longest_streak"]
        total_days = summary["total_days_studied"]

        embed = discord.Embed(
            title=f"🔥 Daily Study Streak: {interaction.user.display_name}",
            description=(
                f"**Current Streak:** 🔥 `{streak} Days`\n"
                f"**Personal Best:** 🏆 `{longest} Days`\n"
                f"**Total Days Studied:** 📅 `{total_days} Days`\n\n"
                f"{'🎉 You have already studied today! Keep up the momentum!' if streak > 0 else '⚠️ You have not logged any study activity today! Use `/study log` to start your streak.'}"
            ),
            color=0xF1C40F if streak > 0 else 0xE74C3C
        )
        embed.set_footer(text="Consistency beats talent • Log daily with /study log")
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(StudyCog(bot))
