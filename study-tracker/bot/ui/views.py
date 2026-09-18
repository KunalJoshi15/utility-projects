from __future__ import annotations
import logging
from typing import Optional, List, Dict, Any
import discord

from database.db import get_db
from services.gamification_service import gamification_service
from services.topic_service import topic_service
from bot.ui.embeds import (
    create_leaderboard_embed,
    create_notes_list_embed,
    create_live_session_ended_embed,
    create_live_session_status_embed
)

logger = logging.getLogger(__name__)

class LeaderboardView(discord.ui.View):
    """Interactive button tabs for switching leaderboard categories."""

    def __init__(self, current_category: str = "topics"):
        super().__init__(timeout=180)
        self.current_category = current_category
        self._update_button_states()

    def _update_button_states(self):
        self.btn_topics.style = discord.ButtonStyle.primary if self.current_category == "topics" else discord.ButtonStyle.secondary
        self.btn_streaks.style = discord.ButtonStyle.primary if self.current_category == "streak" else discord.ButtonStyle.secondary
        self.btn_hours.style = discord.ButtonStyle.primary if self.current_category == "hours" else discord.ButtonStyle.secondary

    @discord.ui.button(label="📚 Top Topics", style=discord.ButtonStyle.primary, custom_id="lb_topics")
    async def btn_topics(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._switch_category(interaction, "topics")

    @discord.ui.button(label="🔥 Longest Streaks", style=discord.ButtonStyle.secondary, custom_id="lb_streaks")
    async def btn_streaks(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._switch_category(interaction, "streak")

    @discord.ui.button(label="⏱️ Study Hours", style=discord.ButtonStyle.secondary, custom_id="lb_hours")
    async def btn_hours(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._switch_category(interaction, "hours")

    async def _switch_category(self, interaction: discord.Interaction, category: str):
        await interaction.response.defer()
        self.current_category = category
        self._update_button_states()

        async with get_db() as db:
            leaderboard_data = await gamification_service.get_leaderboard(db, sort_by=category)

        embed = create_leaderboard_embed(leaderboard_data, category=category)
        await interaction.edit_original_response(embed=embed, view=self)

class NotesPaginationView(discord.ui.View):
    """Interactive pagination view for browsing candidate study notes."""

    def __init__(
        self,
        discord_id: str,
        display_name: str,
        total_count: int,
        search_query: Optional[str] = None,
        page: int = 0,
        page_size: int = 5
    ):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        self.display_name = display_name
        self.total_count = total_count
        self.search_query = search_query
        self.page = page
        self.page_size = page_size
        self._update_button_states()

    def _update_button_states(self):
        max_page = max(0, (self.total_count - 1) // self.page_size)
        self.btn_prev.disabled = self.page <= 0
        self.btn_next.disabled = self.page >= max_page

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, custom_id="notes_prev")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await self._update_page(interaction)

    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary, custom_id="notes_next")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        max_page = max(0, (self.total_count - 1) // self.page_size)
        if self.page < max_page:
            self.page += 1
            await self._update_page(interaction)

    async def _update_page(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self._update_button_states()

        async with get_db() as db:
            offset = self.page * self.page_size
            notes_list, total = await topic_service.get_user_notes(
                db=db,
                discord_id=self.discord_id,
                search_query=self.search_query,
                limit=self.page_size,
                offset=offset
            )

        embed = create_notes_list_embed(
            notes_list=notes_list,
            total_count=total,
            page=self.page,
            query=self.search_query,
            display_name=self.display_name
        )
        await interaction.edit_original_response(embed=embed, view=self)

class LiveSessionControlView(discord.ui.View):
    """Interactive control panel for an active live study session."""

    def __init__(self, discord_id: str, display_name: str):
        super().__init__(timeout=None) # Persistent controls
        self.discord_id = discord_id
        self.display_name = display_name

    @discord.ui.button(label="⏹️ End Study Session", style=discord.ButtonStyle.danger, custom_id="live_session_end")
    async def btn_end_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.discord_id):
            await interaction.response.send_message("❌ This is not your study session!", ephemeral=True)
            return

        await interaction.response.defer()
        from services.live_session_service import live_session_service

        async with get_db() as db:
            try:
                result = await live_session_service.stop_live_session(
                    db=db,
                    discord_id=str(interaction.user.id),
                    username=interaction.user.name,
                    display_name=interaction.user.display_name
                )
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return

        embed = create_live_session_ended_embed(result, interaction.user.display_name or interaction.user.name)
        # Disable buttons on session completion
        self.stop()
        await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="⏱️ Check Status", style=discord.ButtonStyle.secondary, custom_id="live_session_status")
    async def btn_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.discord_id):
            await interaction.response.send_message("❌ This is not your study session!", ephemeral=True)
            return

        from services.live_session_service import live_session_service
        async with get_db() as db:
            session = await live_session_service.get_active_session(db, str(interaction.user.id))

        if not session:
            await interaction.response.send_message("ℹ️ No active session running.", ephemeral=True)
            return

        embed = create_live_session_status_embed(session, interaction.user.display_name or interaction.user.name)
        await interaction.response.send_message(embed=embed, ephemeral=True)
