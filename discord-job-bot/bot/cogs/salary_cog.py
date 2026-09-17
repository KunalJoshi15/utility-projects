import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from database.db import get_db
from services.salary_service import salary_service
from services.profile_service import profile_service
from bot.ui.embeds import create_salary_card_embed, create_salary_comparison_embed

class SalaryCog(commands.GroupCog, group_name="salary"):
    """Commands for salary intelligence and market benchmarks."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="check",
        description="Check authentic AmbitionBox & Glassdoor salary benchmarks for a role and similar roles"
    )
    @app_commands.describe(
        role="Job title / role (e.g. 'Software Engineer', 'Backend Developer', 'Product Manager')",
        company="Specific company to check paygrades for (e.g. 'Google', 'Amazon', 'Flipkart', 'Swiggy')",
        location="Target market location (Default: 'India')"
    )
    async def check_salary(
        self,
        interaction: discord.Interaction,
        role: str,
        company: Optional[str] = None,
        location: Optional[str] = "India"
    ):
        await interaction.response.defer(ephemeral=False)

        benchmarks = salary_service.get_salary_benchmarks(
            role=role,
            company=company,
            location=location
        )

        embed = create_salary_card_embed(benchmarks)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="compare",
        description="Compare salary benchmarks across your dream companies on AmbitionBox & Glassdoor"
    )
    @app_commands.describe(
        role="Job title / role to compare (e.g. 'Software Engineer', 'Data Scientist')",
        custom_companies="Optional comma-separated companies (e.g. 'Google, Microsoft, Amazon, Swiggy')"
    )
    async def compare_salary(
        self,
        interaction: discord.Interaction,
        role: str,
        custom_companies: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=False)

        async with get_db() as db:
            user = await profile_service.get_or_create_profile(
                db=db,
                discord_id=str(interaction.user.id),
                username=interaction.user.name
            )

            comp_list = []
            if custom_companies:
                comp_list = [c.strip() for c in custom_companies.split(",") if c.strip()]
            elif user.target_companies:
                comp_list = [c.strip() for c in user.target_companies.split(",") if c.strip()]

            if not comp_list:
                await interaction.followup.send(
                    "⚠️ **No Target Companies Found!**\n\n"
                    "Please configure your dream companies using `/profile companies names: Google, Microsoft, Amazon, Swiggy` "
                    "or pass them directly: `/salary compare role: 'Software Engineer' custom_companies: 'Google, Microsoft, Amazon'`.",
                    ephemeral=True
                )
                return

            comparison = salary_service.compare_salaries_across_companies(
                role=role,
                companies=comp_list
            )

        embed = create_salary_comparison_embed(comparison)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SalaryCog(bot))
