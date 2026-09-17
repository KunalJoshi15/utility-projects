import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from database.db import get_db
from services.study_service import study_service
from bot.ui.embeds import create_leaderboard_embed

class LeaderboardCog(commands.Cog):
    """Community study leaderboard and rankings."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the server study champion leaderboard by hours & problems solved")
    @app_commands.describe(limit="Number of top candidates to display (default: 10)")
    async def view_leaderboard(self, interaction: discord.Interaction, limit: Optional[int] = 10):
        await interaction.response.defer(ephemeral=False)
        async with get_db() as db:
            board = await study_service.get_leaderboard(db, limit=limit or 10)

        embed = create_leaderboard_embed(board)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
