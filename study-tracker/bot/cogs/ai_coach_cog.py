import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from database.db import get_db
from sqlalchemy import select
from database.models import StudyLog, UserStudyProfile
from services.gemini_coach_service import gemini_coach_service
from bot.ui.embeds import (
    create_study_plan_embed,
    create_quiz_embed,
    create_revision_embed
)
from bot.ui.views import QuizActionView

class AICoachCog(commands.Cog):
    """Gemini AI Interview Coach for custom preparation roadmaps, mock quizzes, and spaced repetition."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="plan", description="Generate an AI-tailored weekly preparation plan for your dream company")
    @app_commands.describe(
        role="Target role (e.g. 'Senior Backend Engineer', 'Full Stack Developer')",
        company="Dream company (e.g. 'Google', 'Amazon', 'Swiggy', 'Uber', 'Stripe')",
        weeks="Preparation timeline in weeks (default: 8)",
        daily_hours="Daily study hours (default: 2.0)"
    )
    async def generate_plan(
        self,
        interaction: discord.Interaction,
        role: Optional[str] = "Senior Backend Engineer",
        company: Optional[str] = "Google",
        weeks: Optional[int] = 8,
        daily_hours: Optional[float] = 2.0
    ):
        await interaction.response.defer(ephemeral=False)
        plan_data = await gemini_coach_service.generate_study_plan(
            target_role=role or "Senior Backend Engineer",
            target_company=company or "Top Tech Company",
            weeks_available=weeks or 8,
            daily_hours=daily_hours or 2.0
        )
        embed = create_study_plan_embed(plan_data)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="quiz", description="AI Technical Concept Quiz: practice answering interview questions")
    @app_commands.describe(
        topic="Specific topic (e.g. 'Strategy Pattern', 'Sliding Window', 'Cache Invalidation', 'ACID')",
        category="Category (LLD, DSA, HLD, Core CS)",
        difficulty="Difficulty (Easy, Medium, Hard)"
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="🏗️ LLD & Design Patterns", value="LLD"),
            app_commands.Choice(name="🧩 DSA Concepts & Tradeoffs", value="DSA"),
            app_commands.Choice(name="🌐 HLD & Distributed Systems", value="HLD"),
            app_commands.Choice(name="💻 Core CS & Concurrency", value="CORE_CS"),
        ],
        difficulty=[
            app_commands.Choice(name="🟢 Easy", value="Easy"),
            app_commands.Choice(name="🟡 Medium", value="Medium"),
            app_commands.Choice(name="🔴 Hard", value="Hard"),
        ]
    )
    async def trigger_quiz(
        self,
        interaction: discord.Interaction,
        topic: str,
        category: Optional[app_commands.Choice[str]] = None,
        difficulty: Optional[app_commands.Choice[str]] = None
    ):
        await interaction.response.defer(ephemeral=False)
        cat_val = category.value if category else "LLD"
        diff_val = difficulty.value if difficulty else "Medium"

        quiz_data = await gemini_coach_service.generate_topic_quiz(
            topic=topic,
            category=cat_val,
            difficulty=diff_val
        )

        embed = create_quiz_embed(quiz_data)
        view = QuizActionView(
            question=quiz_data["question"],
            ideal_points=quiz_data.get("ideal_key_points", []),
            user_id=str(interaction.user.id)
        )
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="revise", description="Spaced Repetition: View topics needing revision today based on confidence scores")
    async def get_revision_queue(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with get_db() as db:
            logs_res = await db.execute(
                select(StudyLog)
                .where(StudyLog.discord_id == str(interaction.user.id))
                .order_by(StudyLog.logged_at.desc())
            )
            logs = list(logs_res.scalars().all())

        queue = gemini_coach_service.get_spaced_repetition_queue(logs)
        embed = create_revision_embed(queue)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AICoachCog(bot))
