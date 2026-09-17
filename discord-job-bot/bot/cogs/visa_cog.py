import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from services.visa_service import visa_service, VISA_SPONSOR_DIRECTORIES
from bot.ui.embeds import (
    create_visa_directory_embed,
    create_visa_jobs_search_embed,
    create_visa_company_intel_embed,
    COLOR_PRIMARY
)

class VisaCog(commands.GroupCog, group_name="visa"):
    """Commands for tracking international visa sponsorship, relocation programs, and verified sponsor registers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="companies",
        description="Browse verified employers offering international Visa Sponsorship & Relocation by country"
    )
    @app_commands.describe(
        country="Destination country (Germany, Netherlands, UK, Canada, USA, Singapore, UAE)"
    )
    @app_commands.choices(
        country=[
            app_commands.Choice(name="🇩🇪 Germany (EU Blue Card)", value="Germany"),
            app_commands.Choice(name="🇳🇱 Netherlands (Highly Skilled Migrant)", value="Netherlands"),
            app_commands.Choice(name="🇬🇧 United Kingdom (Skilled Worker)", value="UK"),
            app_commands.Choice(name="🇨🇦 Canada (Global Talent Stream)", value="Canada"),
            app_commands.Choice(name="🇺🇸 USA (H-1B & L-1 Transfer)", value="USA"),
            app_commands.Choice(name="🇸🇬 Singapore (Employment Pass)", value="Singapore"),
            app_commands.Choice(name="🇦🇪 UAE / Dubai (0% Tax & Golden Visa)", value="UAE"),
        ]
    )
    async def list_companies(
        self,
        interaction: discord.Interaction,
        country: Optional[app_commands.Choice[str]] = None
    ):
        await interaction.response.defer(ephemeral=False)

        country_val = country.value if country else "Germany"
        dir_data = visa_service.get_country_directory(country_val)

        if not dir_data:
            dir_data = VISA_SPONSOR_DIRECTORIES["Germany"]
            country_val = "Germany"

        embed = create_visa_directory_embed(country_val, dir_data)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="jobs",
        description="Search verified international job openings offering Visa Sponsorship and Relocation"
    )
    @app_commands.describe(
        role="Job title (e.g. 'Software Engineer', 'Backend Developer', 'Data Scientist')",
        country="Target country (Germany, Netherlands, UK, Canada, USA, Singapore, UAE)"
    )
    @app_commands.choices(
        country=[
            app_commands.Choice(name="🇩🇪 Germany", value="Germany"),
            app_commands.Choice(name="🇳🇱 Netherlands", value="Netherlands"),
            app_commands.Choice(name="🇬🇧 United Kingdom", value="UK"),
            app_commands.Choice(name="🇨🇦 Canada", value="Canada"),
            app_commands.Choice(name="🇺🇸 USA", value="USA"),
            app_commands.Choice(name="🇸🇬 Singapore", value="Singapore"),
            app_commands.Choice(name="🇦🇪 UAE / Dubai", value="UAE"),
        ]
    )
    async def search_visa_jobs(
        self,
        interaction: discord.Interaction,
        role: str,
        country: Optional[app_commands.Choice[str]] = None
    ):
        await interaction.response.defer(ephemeral=False)

        target_country = country.value if country else "Germany"
        search_data = visa_service.search_visa_jobs(role=role, country=target_country)

        embed = create_visa_jobs_search_embed(search_data)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="policy",
        description="Check official visa sponsorship track record and public registry links for a company"
    )
    @app_commands.describe(
        company="Company name to check (e.g. 'Delivery Hero', 'Booking.com', 'Revolut', 'ASML', 'Shopify')"
    )
    async def check_policy(
        self,
        interaction: discord.Interaction,
        company: str
    ):
        await interaction.response.defer(ephemeral=False)

        intel = visa_service.check_company_visa_intel(company.strip())
        embed = create_visa_company_intel_embed(intel)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(VisaCog(bot))
