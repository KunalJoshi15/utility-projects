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
    create_notes_list_embed,
    create_topics_list_embed
)
from bot.ui.views import NotesPaginationView

logger = logging.getLogger(__name__)

class NotesCog(commands.Cog):
    """Commands for searching and reviewing past study notes & mastered topics."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="notes",
        description="Search and review your past study notes and key takeaways"
    )
    @app_commands.describe(
        query="Keyword to search in your notes (optional)",
        user="View another candidate's public study notes (optional)"
    )
    async def view_notes(
        self,
        interaction: discord.Interaction,
        query: Optional[str] = None,
        user: Optional[discord.User] = None
    ):
        await interaction.response.defer(ephemeral=False)
        target_user = user or interaction.user

        async with get_db() as db:
            notes_list, total_count = await topic_service.get_user_notes(
                db=db,
                discord_id=str(target_user.id),
                search_query=query,
                limit=5,
                offset=0
            )

        name = target_user.display_name or target_user.name
        embed = create_notes_list_embed(
            notes_list=notes_list,
            total_count=total_count,
            page=0,
            query=query,
            display_name=name
        )

        view = NotesPaginationView(
            discord_id=str(target_user.id),
            display_name=name,
            total_count=total_count,
            search_query=query,
            page=0,
            page_size=5
        ) if total_count > 5 else None

        if view:
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="topics",
        description="View the complete checklist of all technical topics you have covered"
    )
    @app_commands.describe(user="View another candidate's mastered topics (optional)")
    async def view_topics(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await interaction.response.defer(ephemeral=False)
        target_user = user or interaction.user

        async with get_db() as db:
            topics_list, total_count = await topic_service.get_user_topics(
                db=db,
                discord_id=str(target_user.id),
                limit=30,
                offset=0
            )
            profile = await topic_service.get_or_create_profile(db, str(target_user.id))
            rank_info = gamification_service.get_rank_info(profile.total_topics_count)

        name = target_user.display_name or target_user.name
        embed = create_topics_list_embed(
            topics_list=topics_list,
            total_count=total_count,
            display_name=name,
            rank_info=rank_info
        )
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(NotesCog(bot))
