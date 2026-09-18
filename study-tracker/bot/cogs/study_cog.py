from __future__ import annotations
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from database.db import get_db
from services.topic_service import topic_service
from services.export_service import export_service
from bot.ui.embeds import (
    create_study_logged_embed,
    create_profile_embed,
    create_session_logs_embed,
    create_session_deleted_embed,
    create_export_ready_embed,
    create_streak_detail_embed
)
from bot.ui.modals import QuickLogModal, EditLogModal
from bot.ui.views import ConfirmResetView, SessionLogsPaginationView, StreakDashboardView

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

    @log_study.autocomplete("topics")
    async def log_topics_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Provides instant autocomplete suggestions from candidate's existing mastered topics."""
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
        name="quicklog",
        description="Open an interactive popup modal to easily enter multiple topics and notes"
    )
    async def quicklog(self, interaction: discord.Interaction):
        modal = QuickLogModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="logs",
        description="Browse, view, and inspect all your past study session logs"
    )
    @app_commands.describe(user="View another candidate's study logs (optional)")
    async def view_logs(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await interaction.response.defer(ephemeral=False)
        target_user = user or interaction.user

        async with get_db() as db:
            sessions, total = await topic_service.get_user_sessions_paginated(
                db=db,
                discord_id=str(target_user.id),
                limit=5,
                offset=0
            )

        embed = create_session_logs_embed(
            sessions=sessions,
            total_count=total,
            page=0,
            display_name=target_user.display_name or target_user.name
        )
        view = SessionLogsPaginationView(
            discord_id=str(target_user.id),
            display_name=target_user.display_name or target_user.name,
            total_count=total,
            page=0,
            page_size=5
        )
        await interaction.followup.send(embed=embed, view=view if total > 5 else None)

    @app_commands.command(
        name="edit",
        description="Edit topics, notes, duration, problems, or category of a past study log"
    )
    @app_commands.describe(id="The ID of the study session to edit (find it with /study logs)")
    async def edit_log(self, interaction: discord.Interaction, id: int):
        async with get_db() as db:
            session = await topic_service.get_session_by_id(
                db=db,
                discord_id=str(interaction.user.id),
                session_id=id
            )

        if not session:
            await interaction.response.send_message(
                f"❌ Study session #{id} was not found or does not belong to you.\nUse `/study logs` to see your valid session IDs.",
                ephemeral=True
            )
            return

        topics_list = session.get("topics", [])
        if len(topics_list) > 1:
            topics_str = "\n".join(f"{i}. {t}" for i, t in enumerate(topics_list, 1))
        elif len(topics_list) == 1:
            topics_str = topics_list[0]
        else:
            topics_str = ""

        modal = EditLogModal(
            session_id=session["id"],
            initial_topics=topics_str,
            initial_notes=session.get("notes"),
            initial_duration=session.get("duration_minutes", 45),
            initial_problems=session.get("problems_solved", 0),
            initial_category=session.get("category", "General")
        )
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="delete",
        description="Delete an accidental or mistakenly added study session log"
    )
    @app_commands.describe(id="The ID of the study session to delete (find it with /study logs)")
    async def delete_log(self, interaction: discord.Interaction, id: int):
        await interaction.response.defer(ephemeral=False)

        async with get_db() as db:
            try:
                result = await topic_service.delete_study_session(
                    db=db,
                    discord_id=str(interaction.user.id),
                    session_id=id
                )
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return
            except Exception as e:
                logger.error(f"Error deleting session #{id}: {e}", exc_info=True)
                await interaction.followup.send("❌ An error occurred while deleting your study session.", ephemeral=True)
                return

        embed = create_session_deleted_embed(result, interaction.user.display_name or interaction.user.name)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="reset",
        description="Reset all your study progress, streak, topics, notes, and badges (Clean slate)"
    )
    async def reset_progress(self, interaction: discord.Interaction):
        view = ConfirmResetView(
            discord_id=str(interaction.user.id),
            display_name=interaction.user.display_name or interaction.user.name
        )
        warning_embed = discord.Embed(
            title="⚠️ Confirm Study Progress Reset",
            description=(
                f"**Warning, {interaction.user.display_name}:**\n\n"
                "Are you sure you want to completely reset all your preparation progress?\n\n"
                "• All your **logged study sessions & topics** will be permanently removed.\n"
                "• All **revision notes & key takeaways** will be deleted.\n"
                "• Your **daily study streak** will reset to `0 Days`.\n"
                "• All **unlocked badges & rank titles** will be reset.\n\n"
                "👉 *Tip: If you only made a mistake on one entry, use `/study delete id:<id>` or `/study edit id:<id>` instead!*"
            ),
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=warning_embed, view=view, ephemeral=True)

    @app_commands.command(
        name="export",
        description="Generate and download a beautifully styled Excel (.xlsx) workbook of your entire study history"
    )
    @app_commands.describe(user="Export another candidate's study history (optional)")
    async def export_document(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await interaction.response.defer(ephemeral=False)
        target_user = user or interaction.user

        async with get_db() as db:
            export_data = await topic_service.get_full_export_data(db, str(target_user.id))

        display_name = target_user.display_name or target_user.name
        excel_buffer = export_service.generate_excel_export(export_data, display_name=display_name)

        clean_username = "".join(c for c in target_user.name if c.isalnum() or c in ('_', '-'))
        filename = f"Study_Tracker_{clean_username}.xlsx"

        file = discord.File(fp=excel_buffer, filename=filename)
        embed = create_export_ready_embed(export_data, display_name)

        await interaction.followup.send(embed=embed, file=file)

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
        description="View your active daily study streak, 7-day consistency calendar & shields"
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

async def setup(bot: commands.Bot):
    await bot.add_cog(StudyCog(bot))

