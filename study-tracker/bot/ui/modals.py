from __future__ import annotations
import logging
from typing import Optional
import discord

from database.db import get_db
from services.topic_service import topic_service
from bot.ui.embeds import create_study_logged_embed

logger = logging.getLogger(__name__)

class QuickLogModal(discord.ui.Modal, title="⚡ Quick Study & Notes Logger"):
    """Interactive modal popup for logging 1 or multiple numbered topics and notes."""

    topics_input = discord.ui.TextInput(
        label="Topics Studied (Number them if multiple)",
        style=discord.TextStyle.paragraph,
        placeholder="1. Factory Design Pattern in Java\n2. Dynamic Programming: 0/1 Knapsack\n3. Redis Pub/Sub",
        required=True,
        max_length=1000
    )

    notes_input = discord.ui.TextInput(
        label="Study Notes & Takeaways (Optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Key learnings, time complexities, code snippets, or takeaways you want to revise later...",
        required=False,
        max_length=2000
    )

    duration_input = discord.ui.TextInput(
        label="Duration in Minutes",
        style=discord.TextStyle.short,
        placeholder="45",
        default="45",
        required=False,
        max_length=5
    )

    problems_input = discord.ui.TextInput(
        label="Problems / Questions Solved",
        style=discord.TextStyle.short,
        placeholder="2",
        default="0",
        required=False,
        max_length=5
    )

    category_input = discord.ui.TextInput(
        label="Category (DSA, LLD, HLD, Cloud, General)",
        style=discord.TextStyle.short,
        placeholder="General",
        default="General",
        required=False,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        try:
            dur = int(self.duration_input.value.strip()) if self.duration_input.value.strip().isdigit() else 45
            probs = int(self.problems_input.value.strip()) if self.problems_input.value.strip().isdigit() else 0
        except ValueError:
            dur, probs = 45, 0

        cat = self.category_input.value.strip() or "General"
        notes_val = self.notes_input.value.strip() if self.notes_input.value.strip() else None

        async with get_db() as db:
            try:
                result = await topic_service.log_study_activity(
                    db=db,
                    discord_id=str(interaction.user.id),
                    raw_topics=self.topics_input.value,
                    notes=notes_val,
                    duration_minutes=dur,
                    problems_solved=probs,
                    category=cat,
                    username=interaction.user.name,
                    display_name=interaction.user.display_name
                )
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return
            except Exception as e:
                logger.error(f"Error logging study modal: {e}", exc_info=True)
                await interaction.followup.send("❌ An error occurred while saving your study session.", ephemeral=True)
                return

        embed = create_study_logged_embed(result, interaction.user.display_name or interaction.user.name)
        await interaction.followup.send(embed=embed)


class EditLogModal(discord.ui.Modal):
    """Interactive modal popup for editing an existing study session log."""

    def __init__(
        self,
        session_id: int,
        initial_topics: str = "",
        initial_notes: Optional[str] = None,
        initial_duration: int = 45,
        initial_problems: int = 0,
        initial_category: str = "General"
    ):
        super().__init__(title=f"✏️ Edit Study Log #{session_id}")
        self.session_id = session_id

        self.topics_input = discord.ui.TextInput(
            label="Topics Studied (Number them if multiple)",
            style=discord.TextStyle.paragraph,
            placeholder="1. Factory Design Pattern in Java\n2. Dynamic Programming",
            default=initial_topics,
            required=True,
            max_length=1000
        )
        self.add_item(self.topics_input)

        self.notes_input = discord.ui.TextInput(
            label="Study Notes & Takeaways (Optional)",
            style=discord.TextStyle.paragraph,
            placeholder="Key learnings, time complexities, code snippets...",
            default=initial_notes or "",
            required=False,
            max_length=2000
        )
        self.add_item(self.notes_input)

        self.duration_input = discord.ui.TextInput(
            label="Duration in Minutes",
            style=discord.TextStyle.short,
            placeholder="45",
            default=str(initial_duration),
            required=False,
            max_length=5
        )
        self.add_item(self.duration_input)

        self.problems_input = discord.ui.TextInput(
            label="Problems / Questions Solved",
            style=discord.TextStyle.short,
            placeholder="2",
            default=str(initial_problems),
            required=False,
            max_length=5
        )
        self.add_item(self.problems_input)

        self.category_input = discord.ui.TextInput(
            label="Category (DSA, LLD, HLD, Cloud, General)",
            style=discord.TextStyle.short,
            placeholder="General",
            default=initial_category,
            required=False,
            max_length=50
        )
        self.add_item(self.category_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        try:
            dur = int(self.duration_input.value.strip()) if self.duration_input.value.strip().isdigit() else 45
            probs = int(self.problems_input.value.strip()) if self.problems_input.value.strip().isdigit() else 0
        except ValueError:
            dur, probs = 45, 0

        cat = self.category_input.value.strip() or "General"
        notes_val = self.notes_input.value.strip() if self.notes_input.value.strip() else None

        from bot.ui.embeds import create_session_edited_embed

        async with get_db() as db:
            try:
                result = await topic_service.edit_study_session(
                    db=db,
                    discord_id=str(interaction.user.id),
                    session_id=self.session_id,
                    new_raw_topics=self.topics_input.value,
                    new_notes=notes_val,
                    new_duration=dur,
                    new_problems=probs,
                    new_category=cat
                )
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return
            except Exception as e:
                logger.error(f"Error editing study modal: {e}", exc_info=True)
                await interaction.followup.send("❌ An error occurred while updating your study session.", ephemeral=True)
                return

        embed = create_session_edited_embed(result, interaction.user.display_name or interaction.user.name)
        await interaction.followup.send(embed=embed)

