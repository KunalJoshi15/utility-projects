import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from database.db import get_db
from database.models import JobApplication
from services.profile_service import profile_service
from bot.ui.embeds import create_applications_list_embed

class ApplicationsCog(commands.GroupCog, group_name="applications"):
    """Commands for tracking and viewing job applications."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="list", description="View your submitted job applications history")
    async def list_applications(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            user = await profile_service.get_or_create_profile(
                db=db,
                discord_id=str(interaction.user.id),
                username=interaction.user.name
            )
            result = await db.execute(
                select(JobApplication)
                .where(JobApplication.discord_id == str(interaction.user.id))
                .order_by(JobApplication.applied_at.desc())
            )
            applications = result.scalars().all()
            embed = create_applications_list_embed(applications, user)

        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ApplicationsCog(bot))
