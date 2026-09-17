import os
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from database.db import get_db
from database.models import ApplyType
from services.job_service import job_service
from services.profile_service import profile_service
from services.apply_service import apply_service
from bot.ui.embeds import (
    create_job_embed,
    create_job_detail_embed,
    create_application_result_embed,
)
from bot.ui.views import JobPaginationView, JobDetailView

class JobsCog(commands.GroupCog, group_name="jobs"):
    """Commands for searching and applying to jobs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="search", description="Search active job listings across LinkedIn, Naukri, Google Jobs & Portals")
    @app_commands.describe(
        query="Job title or keywords (e.g. 'Software Engineer', 'Backend', 'Data Analyst')",
        country="Target country (India, USA, UK, Canada, Germany, Remote)",
        location="Target city or state (e.g. 'Bengaluru', 'Hyderabad', 'Pune', 'Mumbai', 'Delhi NCR', 'San Francisco')",
        employment_type="Employment type (Full-time, Internship, Contract, Part-time)",
        min_salary="Minimum target salary / payscale (e.g. '₹ 25 LPA', '₹ 15 LPA', '$140k')",
        company="Specific target company (e.g. 'Google', 'Amazon', 'Microsoft', 'Flipkart')",
        remote="Filter strictly for remote positions"
    )
    @app_commands.choices(
        country=[
            app_commands.Choice(name="🇮🇳 India", value="India"),
            app_commands.Choice(name="🇺🇸 USA", value="USA"),
            app_commands.Choice(name="🇬🇧 United Kingdom", value="UK"),
            app_commands.Choice(name="🇨🇦 Canada", value="Canada"),
            app_commands.Choice(name="🇩🇪 Germany", value="Germany"),
            app_commands.Choice(name="🌐 Worldwide / Remote", value="Remote"),
        ],
        employment_type=[
            app_commands.Choice(name="Full-time", value="FULLTIME"),
            app_commands.Choice(name="Internship", value="INTERN"),
            app_commands.Choice(name="Contract", value="CONTRACTOR"),
            app_commands.Choice(name="Part-time", value="PARTTIME"),
        ]
    )
    async def search(
        self,
        interaction: discord.Interaction,
        query: str,
        country: Optional[app_commands.Choice[str]] = None,
        location: Optional[str] = None,
        employment_type: Optional[app_commands.Choice[str]] = None,
        min_salary: Optional[str] = None,
        company: Optional[str] = None,
        remote: bool = False
    ):
        await interaction.response.defer(ephemeral=False)

        country_val = country.value if country else None
        emp_val = employment_type.value if employment_type else None
        
        async with get_db() as db:
            # Fallback to user's saved country in profile if not specified
            if not country_val:
                user = await profile_service.get_profile(db, str(interaction.user.id))
                if user and user.country:
                    country_val = user.country

            jobs = await job_service.search_jobs(
                db=db,
                query=query,
                country=country_val,
                location=location,
                company_filter=company,
                min_salary=min_salary,
                employment_type=emp_val,
                is_remote=remote,
                limit=10
            )

        if not jobs:
            loc_text = f" in {location}" if location else ""
            cnt_text = f" ({country_val or 'India'})"
            await interaction.followup.send(
                f"❌ No jobs found matching **'{query}'**{loc_text}{cnt_text}. Try broader keywords or change the location filter.",
                ephemeral=True
            )
            return

        first_job = jobs[0]
        embed = create_job_embed(first_job, 1, len(jobs))
        view = JobPaginationView(jobs=jobs, user_id=str(interaction.user.id))

        filter_badges = [f"**Query:** `{query}`"]
        if country_val:
            filter_badges.append(f"**Country:** `{country_val}`")
        if location:
            filter_badges.append(f"**City:** `{location}`")
        if emp_val:
            filter_badges.append(f"**Type:** `{emp_val}`")
        if min_salary:
            filter_badges.append(f"**Salary:** `{min_salary}`")
        if company:
            filter_badges.append(f"**Company:** `{company}`")
        if remote:
            filter_badges.append("`🏠 Remote`")

        header = f"🔍 Found **{len(jobs)}** positions across **LinkedIn, Naukri & Portals**\n" + " • ".join(filter_badges) + ":"
        await interaction.followup.send(
            content=header,
            embed=embed,
            view=view
        )

    @app_commands.command(name="match", description="Search jobs on LinkedIn, Naukri & Portals matching your uploaded resume")
    async def match_jobs(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        async with get_db() as db:
            user = await profile_service.get_profile(db, str(interaction.user.id))
            if not user or not user.resume_file_path:
                await interaction.followup.send(
                    "❌ **Resume Required!** Please upload your resume first using `/profile resume` to enable AI job matching.",
                    ephemeral=True
                )
                return

            jobs = await job_service.search_jobs_for_resume(db=db, user=user, limit=10)

        if not jobs:
            await interaction.followup.send(
                "❌ No matching jobs found based on your resume skills right now. Try `/jobs search` with custom keywords.",
                ephemeral=True
            )
            return

        first_job = jobs[0]
        embed = create_job_embed(first_job, 1, len(jobs))
        view = JobPaginationView(jobs=jobs, user_id=str(interaction.user.id))

        await interaction.followup.send(
            content=f"🎯 **Resume Matched Openings** for **{user.full_name or user.username}** (LinkedIn & Naukri Feeds):",
            embed=embed,
            view=view
        )

    @app_commands.command(name="view", description="View full job description and requirements by Job ID")
    @app_commands.describe(job_id="The unique ID of the job")
    async def view(self, interaction: discord.Interaction, job_id: str):
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            job = await job_service.get_job_by_id(db, job_id.strip())

        if not job:
            await interaction.followup.send(
                f"❌ Could not find job with ID `{job_id}`. Run `/jobs search` to find active job IDs.",
                ephemeral=True
            )
            return

        embed = create_job_detail_embed(job)
        view = JobDetailView(job=job, user_id=str(interaction.user.id))
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="apply", description="Auto-apply to a job opening using your stored profile and resume")
    @app_commands.describe(
        job_id="The unique ID of the job",
        auto_submit="Automatically click the final submit button (Default: True)"
    )
    async def apply(self, interaction: discord.Interaction, job_id: str, auto_submit: bool = True):
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            user = await profile_service.get_profile(db, str(interaction.user.id))
            if not user or not user.resume_file_path:
                await interaction.followup.send(
                    "❌ **Resume Required!** Please upload your resume first using `/profile resume` or configure your details with `/profile setup`.",
                    ephemeral=True
                )
                return

            job = await job_service.get_job_by_id(db, job_id.strip())
            if not job:
                await interaction.followup.send(
                    f"❌ Could not find job with ID `{job_id}`. Please check the ID from `/jobs search`.",
                    ephemeral=True
                )
                return

            await interaction.followup.send(
                f"⏳ Starting automated application for **{job.title}** @ **{job.company}**...\n"
                f"Using mechanism: `{job.apply_type}`. Please wait while our headless browser processes the form.",
                ephemeral=True
            )

            # Execute the Playwright application flow
            result = await apply_service.execute_application(
                db=db,
                user=user,
                job=job,
                auto_submit=auto_submit
            )

            embed = create_application_result_embed(result, job, user)
            
            # If screenshot was captured, attach it to response
            screenshot_path = result.get("screenshot_path")
            file_to_send = None
            if screenshot_path and os.path.exists(screenshot_path):
                file_to_send = discord.File(screenshot_path, filename="application_proof.png")
                embed.set_image(url="attachment://application_proof.png")

            if file_to_send:
                await interaction.channel.send(
                    content=f"{interaction.user.mention} Application update:",
                    embed=embed,
                    file=file_to_send
                )
            else:
                await interaction.channel.send(
                    content=f"{interaction.user.mention} Application update:",
                    embed=embed
                )

async def setup(bot: commands.Bot):
    await bot.add_cog(JobsCog(bot))
