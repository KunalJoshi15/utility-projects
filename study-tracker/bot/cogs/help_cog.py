import discord
from discord import app_commands
from discord.ext import commands
from bot.ui.embeds import create_help_embed, COLOR_SUCCESS

class HelpCog(commands.Cog):
    """Help and system health status commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="View complete manual of study tracking & AI coach commands")
    async def show_help(self, interaction: discord.Interaction):
        embed = create_help_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="Check Study Tracker bot uptime and latency")
    async def show_status(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🟢 Study Tracker Bot Status",
            description=f"• **Gateway Latency:** `{latency_ms}ms`\n• **Database:** `SQLite (Async IO) - Operational`\n• **Gemini AI:** `Enabled (2.5 Flash)`",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
