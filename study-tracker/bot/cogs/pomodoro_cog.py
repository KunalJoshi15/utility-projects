import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from services.pomodoro_service import pomodoro_service
from bot.ui.embeds import create_pomodoro_embed
from bot.ui.views import PomodoroView

class PomodoroCog(commands.Cog):
    """Focus study timers with automatic progress logging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="timer", description="Start a focused study session timer with 1-click automatic logging")
    @app_commands.describe(
        duration="Duration in minutes (e.g. 25, 45, 60)",
        task="What problem or topic you are focusing on",
        category="Category (DSA, LLD, HLD, Core CS)"
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="🧩 DSA", value="DSA"),
            app_commands.Choice(name="🏗️ LLD", value="LLD"),
            app_commands.Choice(name="🌐 HLD", value="HLD"),
            app_commands.Choice(name="💻 Core CS", value="CORE_CS"),
        ]
    )
    async def start_timer(
        self,
        interaction: discord.Interaction,
        duration: Optional[int] = 25,
        task: Optional[str] = "Deep Work Session",
        category: Optional[app_commands.Choice[str]] = None
    ):
        dur = max(5, min(180, duration or 25))
        cat_val = category.value if category else "DSA"

        session_data = pomodoro_service.start_session(
            discord_id=str(interaction.user.id),
            task_description=task or "Deep Work Session",
            category=cat_val,
            duration_minutes=dur
        )

        embed = create_pomodoro_embed(session_data)
        view = PomodoroView(user_id=str(interaction.user.id))

        await interaction.response.send_message(
            content=f"🔔 <@{interaction.user.id}> **Focus Mode Activated!** `{dur} Minutes` on **{session_data['task']}**.",
            embed=embed,
            view=view
        )

    @app_commands.command(name="pomodoro", description="Start a standard 25-minute Pomodoro study block")
    @app_commands.describe(task="Task or problem name (e.g. 'LeetCode Tree Problems' or 'Factory Pattern LLD')")
    async def start_pomodoro(self, interaction: discord.Interaction, task: Optional[str] = "Pomodoro Study Block"):
        session_data = pomodoro_service.start_session(
            discord_id=str(interaction.user.id),
            task_description=task or "Pomodoro Study Block",
            category="DSA",
            duration_minutes=25
        )
        embed = create_pomodoro_embed(session_data)
        view = PomodoroView(user_id=str(interaction.user.id))

        await interaction.response.send_message(
            content=f"🍅 <@{interaction.user.id}> **25-Minute Pomodoro Started!**",
            embed=embed,
            view=view
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(PomodoroCog(bot))
