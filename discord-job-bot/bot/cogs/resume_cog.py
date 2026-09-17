import discord
from typing import Optional
from discord import app_commands
from discord.ext import commands
from database.db import get_db
from services.profile_service import profile_service
from services.gemini_service import gemini_service
from bot.ui.embeds import create_resume_review_embed, create_resume_parsed_embed

class ResumeCog(commands.GroupCog, group_name="resume"):
    """Commands for Gemini AI resume analysis, review, and parsing."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="review", description="Get a deep Gemini AI audit of your resume: flaws, ATS score & rewrites")
    async def review_resume(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            user = await profile_service.get_profile(db, str(interaction.user.id))
            if not user or not user.resume_file_path:
                await interaction.followup.send(
                    "❌ **No Resume Uploaded!** Please upload your resume first using `/profile resume`.",
                    ephemeral=True
                )
                return

            # Extract text and analyze with Gemini AI
            resume_text = gemini_service.extract_text_from_file(user.resume_file_path)
            review_data = await gemini_service.analyze_resume(resume_text)
            embed = create_resume_review_embed(review_data, user.full_name or user.username)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="parse", description="Extract skills and role from your resume to update your profile")
    async def parse_resume(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            user = await profile_service.get_profile(db, str(interaction.user.id))
            if not user or not user.resume_file_path:
                await interaction.followup.send(
                    "❌ **No Resume Uploaded!** Please upload your resume first using `/profile resume`.",
                    ephemeral=True
                )
                return

            resume_text = gemini_service.extract_text_from_file(user.resume_file_path)
            profile_data = await gemini_service.extract_resume_profile(resume_text)

            # Update profile in DB with extracted data
            await profile_service.update_profile(
                db=db,
                discord_id=str(interaction.user.id),
                username=interaction.user.name,
                current_role=profile_data.get("primary_role"),
                years_of_experience=profile_data.get("years_of_experience", 0)
            )

            embed = create_resume_parsed_embed(profile_data, user.full_name or user.username)

        await interaction.followup.send(
            content="✅ **Your profile has been synchronized with your resume!**",
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(
        name="fit",
        description="Audit if your resume is a good fit for a specific job profile, tech stack or opening"
    )
    @app_commands.describe(
        job_id="Optional: unique ID of a job from /jobs search to evaluate against",
        target_role="Target role (e.g. 'Senior Backend Engineer')",
        job_description="Job requirements or description to compare against your resume",
        company="Company name (optional)"
    )
    async def check_fit(
        self,
        interaction: discord.Interaction,
        job_id: Optional[str] = None,
        target_role: Optional[str] = None,
        job_description: Optional[str] = None,
        company: Optional[str] = None
    ):
        # If no arguments are provided, open interactive modal
        if not job_id and not target_role and not job_description:
            from bot.ui.modals import ResumeJobFitModal
            modal = ResumeJobFitModal()
            await interaction.response.send_modal(modal)
            return

        await interaction.response.defer(ephemeral=True)

        from services.job_service import job_service
        from bot.ui.embeds import create_resume_job_fit_embed

        async with get_db() as db:
            user = await profile_service.get_profile(db, str(interaction.user.id))
            if not user or not user.resume_file_path:
                await interaction.followup.send(
                    "❌ **Resume Required!** Please upload your resume first using `/profile resume`.",
                    ephemeral=True
                )
                return

            role_to_check = target_role or user.current_role or "Software Engineer"
            desc_to_check = job_description
            comp_to_check = company

            if job_id:
                job = await job_service.get_job_by_id(db, job_id.strip())
                if job:
                    role_to_check = job.title
                    desc_to_check = job.description
                    comp_to_check = job.company

            resume_text = gemini_service.extract_text_from_file(user.resume_file_path)
            fit_data = await gemini_service.evaluate_resume_fit_for_job(
                resume_text=resume_text,
                target_role=role_to_check,
                job_description=desc_to_check,
                company=comp_to_check
            )

        embed = create_resume_job_fit_embed(fit_data, user.full_name or user.username)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ResumeCog(bot))
