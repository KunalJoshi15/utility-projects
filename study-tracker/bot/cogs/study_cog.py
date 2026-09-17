import discord
from typing import Optional
from discord import app_commands
from discord.ext import commands
from database.db import get_db
from services.study_service import study_service
from bot.ui.embeds import (
    create_progress_embed,
    create_streak_embed,
    create_roadmap_embed,
    COLOR_SUCCESS,
    COLOR_PRIMARY
)
from bot.ui.modals import QuickStudyLogModal, CreateGoalModal
from bot.ui.views import RoadmapSelectView

CATEGORY_CHOICES = [
    app_commands.Choice(name="🧩 DSA (Data Structures & Algorithms)", value="DSA"),
    app_commands.Choice(name="🏗️ LLD (Low-Level Design & Patterns)", value="LLD"),
    app_commands.Choice(name="🌐 HLD (High-Level System Design)", value="HLD"),
    app_commands.Choice(name="💻 Core CS (OS, DBMS, Concurrency)", value="CORE_CS"),
    app_commands.Choice(name="🎤 Mock Interview & Behavioral", value="MOCK_INTERVIEW"),
    app_commands.Choice(name="🎯 Custom Topic", value="CUSTOM"),
]

CONFIDENCE_CHOICES = [
    app_commands.Choice(name="⭐ 1 Star (Struggled / Needs Review)", value=1),
    app_commands.Choice(name="⭐⭐ 2 Stars (Partial Solution)", value=2),
    app_commands.Choice(name="⭐⭐⭐ 3 Stars (Solved with Hints)", value=3),
    app_commands.Choice(name="⭐⭐⭐⭐ 4 Stars (Clean Solution - Good)", value=4),
    app_commands.Choice(name="⭐⭐⭐⭐⭐ 5 Stars (Optimal / Mastered)", value=5),
]

class StudyCog(commands.GroupCog, group_name="study"):
    """Commands for logging interview preparation, tracking roadmaps, streaks, and goals."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="log", description="Log a completed interview preparation study session")
    @app_commands.describe(
        category="Category of preparation (DSA, LLD, HLD, Core CS)",
        topic="Subject or topic studied (e.g. 'Dynamic Programming', 'Observer Pattern', 'Rate Limiter')",
        problems="Number of problems solved (default: 1)",
        minutes="Duration spent in minutes (default: 30)",
        confidence="How confident you feel with this topic (1 to 5 Stars)",
        problem_name="Specific problem name or link (e.g. 'Coin Change II', 'Parking Lot LLD')",
        notes="Key takeaways, time/space complexity, or design decisions"
    )
    @app_commands.choices(
        category=CATEGORY_CHOICES,
        confidence=CONFIDENCE_CHOICES
    )
    async def log_study(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        topic: str,
        problems: Optional[int] = 1,
        minutes: Optional[int] = 30,
        confidence: Optional[app_commands.Choice[int]] = None,
        problem_name: Optional[str] = None,
        notes: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=True)
        conf_val = confidence.value if confidence else 4

        async with get_db() as db:
            log = await study_service.log_session(
                db=db,
                discord_id=str(interaction.user.id),
                category=category.value,
                topic=topic,
                subtopic_or_problem=problem_name,
                duration_minutes=minutes or 30,
                problems_solved=problems or 1,
                confidence_score=conf_val,
                notes=notes,
                username=interaction.user.name
            )
            summary = await study_service.get_user_progress_summary(db, str(interaction.user.id))

        embed = create_progress_embed(summary)
        await interaction.followup.send(
            content=f"✅ **Session Logged:** `{log.problems_solved} problem(s)` • `{log.duration_minutes}m` on **{log.topic}** ({'⭐'*conf_val})!",
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(name="quicklog", description="Open quick popup modal to log your preparation session")
    async def quick_log(self, interaction: discord.Interaction):
        await interaction.response.send_modal(QuickStudyLogModal())

    @app_commands.command(name="progress", description="View your visual preparation scorecard, streaks, and hours")
    @app_commands.describe(user="View another candidate's progress (optional)")
    async def view_progress(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        await interaction.response.defer(ephemeral=False)
        target_id = str(user.id) if user else str(interaction.user.id)

        async with get_db() as db:
            summary = await study_service.get_user_progress_summary(db, target_id)

        embed = create_progress_embed(summary)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="streak", description="Check your daily preparation streak and milestone badge")
    async def view_streak(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        async with get_db() as db:
            streak_data = await study_service.get_streak_status(db, str(interaction.user.id))

        embed = create_streak_embed(streak_data, interaction.user.display_name or interaction.user.name)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="roadmap", description="Browse structured preparation roadmaps for DSA, LLD, HLD & Core CS")
    @app_commands.describe(category="Select curriculum category")
    @app_commands.choices(
        category=[
            app_commands.Choice(name="🧩 DSA (Data Structures & Algorithms)", value="DSA"),
            app_commands.Choice(name="🏗️ LLD (Low-Level Design & Patterns)", value="LLD"),
            app_commands.Choice(name="🌐 HLD (High-Level System Design)", value="HLD"),
            app_commands.Choice(name="💻 Core CS (OS, DBMS, Concurrency)", value="CORE_CS"),
        ]
    )
    async def view_roadmap(self, interaction: discord.Interaction, category: Optional[app_commands.Choice[str]] = None):
        await interaction.response.defer(ephemeral=False)
        cat_key = category.value if category else "DSA"
        roadmap = study_service.get_curated_roadmaps(cat_key)
        embed = create_roadmap_embed(roadmap)
        view = RoadmapSelectView()
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="goals", description="View and track your active preparation goals and milestones")
    async def list_goals(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with get_db() as db:
            goals = await study_service.get_goals(db, str(interaction.user.id))

        if not goals:
            await interaction.followup.send(
                "ℹ️ You have no active goals set. Create one with `/study goal_create`!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎯 Your Preparation Goals & Targets",
            description="Track your personal milestones across DSA, LLD, and System Design:",
            color=COLOR_PRIMARY
        )

        for g in goals:
            pct = (g.current_count / g.target_count) * 100.0 if g.target_count > 0 else 0
            status_emoji = "✅ Completed" if g.is_completed else f"`{g.current_count}/{g.target_count} {g.unit}` ({pct:.0f}%)"
            deadline_text = f" • Due: `{g.deadline}`" if g.deadline else ""
            embed.add_field(
                name=f"Goal #{g.id}: {g.title}",
                value=f"• **Category:** `{g.category}` • **Status:** {status_emoji}{deadline_text}",
                inline=False
            )

        embed.set_footer(text="Create new goals with /study goal_create")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="goal_create", description="Create a new preparation milestone target")
    async def create_goal_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreateGoalModal())

    @app_commands.command(name="profile", description="Configure your preparation target role and dream companies")
    @app_commands.describe(
        name="Your name (Discord ID is auto-populated)",
        target_role="Target role (e.g. 'Senior Backend Engineer', 'SDE-2')",
        target_companies="Dream companies (e.g. 'Google, Microsoft, Amazon, Swiggy')"
    )
    async def configure_profile(
        self,
        interaction: discord.Interaction,
        name: Optional[str] = None,
        target_role: Optional[str] = None,
        target_companies: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=True)
        display = name or interaction.user.display_name or interaction.user.name

        async with get_db() as db:
            profile = await study_service.update_profile(
                db=db,
                discord_id=str(interaction.user.id),
                username=interaction.user.name,
                display_name=display,
                target_role=target_role,
                target_companies=target_companies
            )
            summary = await study_service.get_user_progress_summary(db, str(interaction.user.id))

        embed = create_progress_embed(summary)
        await interaction.followup.send(
            content=f"✅ **Candidate Study Profile Updated!**\n"
                    f"• **Name:** `{profile.display_name}`\n"
                    f"• **Discord ID:** `{interaction.user.id}` (Auto-linked)\n"
                    f"• **Target Role:** `{profile.target_role}`\n"
                    f"• **Dream Companies:** `{profile.target_companies}`",
            embed=embed,
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(StudyCog(bot))
