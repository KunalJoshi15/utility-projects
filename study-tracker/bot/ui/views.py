import discord
from database.db import get_db
from services.pomodoro_service import pomodoro_service
from services.study_service import study_service
from services.gemini_coach_service import gemini_coach_service
from bot.ui.modals import QuizAnswerModal
from bot.ui.embeds import create_roadmap_embed, create_quiz_embed, create_progress_embed

class PomodoroView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=3600)
        self.user_id = user_id

    @discord.ui.button(label="✅ Complete & Log Session", style=discord.ButtonStyle.success, emoji="⏱️")
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your focus session!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        async with get_db() as db:
            sess = await pomodoro_service.complete_session(db, self.user_id)
            if sess:
                summary = await study_service.get_user_progress_summary(db, self.user_id)
                embed = create_progress_embed(summary)
                await interaction.followup.send(
                    f"🎉 **Great Focus Session!** Completed and logged `{sess['duration_minutes']}m` on **{sess['task']}**.",
                    embed=embed,
                    ephemeral=True
                )
            else:
                await interaction.followup.send("⚠️ No active session found or already completed.", ephemeral=True)

        self.stop()

    @discord.ui.button(label="❌ Cancel Timer", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your focus session!", ephemeral=True)
            return

        pomodoro_service.cancel_session(self.user_id)
        await interaction.response.send_message("⏹️ **Focus session cancelled.**", ephemeral=True)
        self.stop()

class RoadmapSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.select(
        placeholder="Select a preparation roadmap category...",
        options=[
            discord.SelectOption(label="Data Structures & Algorithms", value="DSA", emoji="🧩", description="Arrays, Trees, Graphs, DP"),
            discord.SelectOption(label="Low-Level Design & Patterns", value="LLD", emoji="🏗️", description="SOLID, Design Patterns, Machine Coding"),
            discord.SelectOption(label="High-Level System Design", value="HLD", emoji="🌐", description="Distributed Systems, Caching, URL Shortener"),
            discord.SelectOption(label="CS Fundamentals & Concurrency", value="CORE_CS", emoji="💻", description="Threads, OS, DBMS, Networks"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        cat = select.values[0]
        roadmap = study_service.get_curated_roadmaps(cat)
        embed = create_roadmap_embed(roadmap)
        await interaction.response.edit_message(embed=embed, view=self)

class QuizActionView(discord.ui.View):
    def __init__(self, question: str, ideal_points: list, user_id: str):
        super().__init__(timeout=600)
        self.question = question
        self.ideal_points = ideal_points
        self.user_id = user_id

    @discord.ui.button(label="💡 Submit Answer for AI Grading", style=discord.ButtonStyle.primary, emoji="✍️")
    async def answer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Please run your own `/study quiz` command to answer!", ephemeral=True)
            return
        await interaction.response.send_modal(QuizAnswerModal(self.question, self.ideal_points))
