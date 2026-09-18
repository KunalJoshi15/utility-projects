from __future__ import annotations
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from database.db import get_db
from services.live_session_service import live_session_service
from bot.ui.embeds import (
    create_live_session_started_embed,
    create_live_session_ended_embed,
    create_live_session_status_embed
)
from bot.ui.views import LiveSessionControlView

logger = logging.getLogger(__name__)

class SessionCog(commands.GroupCog, group_name="session"):
    """Real-time live study sessions with manual stop and offline auto-stop."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="start",
        description="Start a real-time live study session (Auto-stops if you go offline!)"
    )
    @app_commands.describe(
        topic="What you are studying (e.g. 'LRU Cache Design', 'LeetCode Trees', 'System Design')",
        category="Domain (DSA, LLD, HLD, Cloud, General)"
    )
    async def start_session(
        self,
        interaction: discord.Interaction,
        topic: Optional[str] = "General Study",
        category: Optional[str] = "General"
    ):
        await interaction.response.defer(ephemeral=False)

        async with get_db() as db:
            try:
                session = await live_session_service.start_live_session(
                    db=db,
                    discord_id=str(interaction.user.id),
                    guild_id=str(interaction.guild_id) if interaction.guild_id else None,
                    channel_id=str(interaction.channel_id) if interaction.channel_id else None,
                    topic_or_goal=topic or "General Study",
                    category=category or "General"
                )
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return
            except Exception as e:
                logger.error(f"Error starting live session: {e}", exc_info=True)
                await interaction.followup.send("❌ An error occurred while starting your live study session.", ephemeral=True)
                return

        name = interaction.user.display_name or interaction.user.name
        embed = create_live_session_started_embed(session, name)
        view = LiveSessionControlView(discord_id=str(interaction.user.id), display_name=name)
        await interaction.followup.send(embed=embed, view=view)

    @start_session.autocomplete("topic")
    async def start_topic_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        try:
            async with get_db() as db:
                topics = await topic_service.get_user_existing_topics_autocomplete(
                    db=db,
                    discord_id=str(interaction.user.id),
                    current_query=current
                )
            return [app_commands.Choice(name=t[:100], value=t[:100]) for t in topics]
        except Exception:
            return []

    @app_commands.command(
        name="stop",
        description="Conclude your active live study session and log your minutes"
    )
    @app_commands.describe(
        notes="Key takeaways, learnings, or revision notes (optional)",
        topics="Specific topics covered if different from goal (optional)",
        problems="Coding problems / design questions solved (default: 0)"
    )
    async def stop_session(
        self,
        interaction: discord.Interaction,
        notes: Optional[str] = None,
        topics: Optional[str] = None,
        problems: Optional[int] = 0
    ):
        await interaction.response.defer(ephemeral=False)

        async with get_db() as db:
            try:
                result = await live_session_service.stop_live_session(
                    db=db,
                    discord_id=str(interaction.user.id),
                    notes=notes,
                    raw_topics=topics,
                    problems_solved=problems or 0,
                    username=interaction.user.name,
                    display_name=interaction.user.display_name
                )
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return
            except Exception as e:
                logger.error(f"Error stopping live session: {e}", exc_info=True)
                await interaction.followup.send("❌ An error occurred while ending your study session.", ephemeral=True)
                return

        embed = create_live_session_ended_embed(result, interaction.user.display_name or interaction.user.name)
        await interaction.followup.send(embed=embed)

    @stop_session.autocomplete("topics")
    async def stop_topics_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        try:
            async with get_db() as db:
                topics = await topic_service.get_user_existing_topics_autocomplete(
                    db=db,
                    discord_id=str(interaction.user.id),
                    current_query=current
                )
            return [app_commands.Choice(name=t[:100], value=t[:100]) for t in topics]
        except Exception:
            return []

    @app_commands.command(
        name="status",
        description="Check your current live study session timer and elapsed time"
    )
    async def status_session(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            session = await live_session_service.get_active_session(db, str(interaction.user.id))

        if not session:
            await interaction.followup.send("ℹ️ You do not have an active study session running. Start one with `/session start`!", ephemeral=True)
            return

        embed = create_live_session_status_embed(session, interaction.user.display_name or interaction.user.name)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Auto-stop active live study session if member goes offline."""
        if after.bot:
            return

        if after.status == discord.Status.offline and before.status != discord.Status.offline:
            user_id = str(after.id)
            async with get_db() as db:
                session = await live_session_service.get_active_session(db, user_id)
                if session:
                    logger.info(f"User {after.display_name} ({user_id}) went offline. Auto-concluding study session.")
                    await live_session_service.auto_stop_offline_session(
                        bot=self.bot,
                        db=db,
                        session=session,
                        reason="Went Offline on Discord"
                    )

async def setup(bot: commands.Bot):
    await bot.add_cog(SessionCog(bot))
