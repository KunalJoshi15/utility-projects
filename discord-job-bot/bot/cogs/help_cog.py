import discord
from discord import app_commands
from discord.ext import commands
import time
from bot.ui.embeds import create_help_embed, COLOR_SUCCESS

class HelpCog(commands.Cog):
    """Commands for assistance and bot status."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="help", description="Show full guide on how to search jobs and auto-apply")
    async def help_command(self, interaction: discord.Interaction):
        embed = create_help_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="Show bot health, latency, and uptime")
    async def status_command(self, interaction: discord.Interaction):
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        latency_ms = round(self.bot.latency * 1000, 2)

        embed = discord.Embed(
            title="⚡ Bot System Status",
            description="Operational and ready to process job applications.",
            color=COLOR_SUCCESS
        )
        embed.add_field(name="Gateway Latency", value=f"`{latency_ms} ms`", inline=True)
        embed.add_field(name="Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="Active Guilds", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="Browser Engine", value="`Playwright Headless Chromium`", inline=False)
        embed.add_field(name="Cloud Platform", value="`Google Cloud Platform (GCP)`", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
