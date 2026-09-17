import discord
from typing import List, Optional
from database.models import CachedJob, ApplyType
from bot.ui.embeds import create_job_embed, create_job_detail_embed

class JobPaginationView(discord.ui.View):
    def __init__(self, jobs: List[CachedJob], user_id: str, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.jobs = jobs
        self.user_id = str(user_id)
        self.current_index = 0
        self.link_button = None
        self._refresh_components()

    def _refresh_components(self):
        current_job = self.jobs[self.current_index]
        self.prev_button.disabled = self.current_index == 0
        self.next_button.disabled = self.current_index >= len(self.jobs) - 1

        # Remove existing dynamic link button if present
        if self.link_button:
            self.remove_item(self.link_button)

        # Add link button for current job
        self.link_button = discord.ui.Button(
            label="🔗 Open Listing",
            style=discord.ButtonStyle.link,
            url=current_job.apply_url
        )
        self.add_item(self.link_button)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, custom_id="job_prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This job search pagination belongs to another user. Run `/jobs search` to create your own.", ephemeral=True)
            return

        if self.current_index > 0:
            self.current_index -= 1
            self._refresh_components()
            embed = create_job_embed(self.jobs[self.current_index], self.current_index + 1, len(self.jobs))
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, custom_id="job_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This job search pagination belongs to another user. Run `/jobs search` to create your own.", ephemeral=True)
            return

        if self.current_index < len(self.jobs) - 1:
            self.current_index += 1
            self._refresh_components()
            embed = create_job_embed(self.jobs[self.current_index], self.current_index + 1, len(self.jobs))
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚡ Apply Now", style=discord.ButtonStyle.success, custom_id="job_apply")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_job = self.jobs[self.current_index]
        await interaction.response.send_message(
            f"🚀 Initiating auto-apply for **{current_job.title}** @ **{current_job.company}** (ID: `{current_job.job_id}`)...\n"
            f"Run `/jobs apply {current_job.job_id}` for full tracking or wait while we prepare your application.",
            ephemeral=True
        )

    @discord.ui.button(label="📄 Details", style=discord.ButtonStyle.primary, custom_id="job_details")
    async def details_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_job = self.jobs[self.current_index]
        embed = create_job_detail_embed(current_job)
        view = JobDetailView(current_job, self.user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🎯 Check Resume Fit", style=discord.ButtonStyle.secondary, custom_id="job_check_fit")
    async def check_fit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        current_job = self.jobs[self.current_index]
        
        from database.db import get_db
        from services.profile_service import profile_service
        from services.gemini_service import gemini_service
        from bot.ui.embeds import create_resume_job_fit_embed

        async with get_db() as db:
            user = await profile_service.get_profile(db, str(interaction.user.id))
            if not user or not user.resume_file_path:
                await interaction.followup.send(
                    "❌ **Resume Required!** Please upload your resume first using `/profile resume` to evaluate your fit for this job.",
                    ephemeral=True
                )
                return

            resume_text = gemini_service.extract_text_from_file(user.resume_file_path)
            fit_data = await gemini_service.evaluate_resume_fit_for_job(
                resume_text=resume_text,
                target_role=current_job.title,
                job_description=current_job.description,
                company=current_job.company
            )

        embed = create_resume_job_fit_embed(fit_data, user.full_name or user.username)
        await interaction.followup.send(embed=embed, ephemeral=True)


class JobDetailView(discord.ui.View):
    def __init__(self, job: CachedJob, user_id: str, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.job = job
        self.user_id = str(user_id)
        
        # Add dynamic link button
        self.add_item(discord.ui.Button(label="🔗 Open Listing", style=discord.ButtonStyle.link, url=job.apply_url))

    @discord.ui.button(label="⚡ Auto-Apply", style=discord.ButtonStyle.success, custom_id="detail_apply")
    async def apply_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"⏳ To execute your application with full error reporting and screenshot verification, run:\n"
            f"`/jobs apply {self.job.job_id}`",
            ephemeral=True
        )

    @discord.ui.button(label="🎯 Check Resume Fit", style=discord.ButtonStyle.secondary, custom_id="detail_check_fit")
    async def check_fit_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        from database.db import get_db
        from services.profile_service import profile_service
        from services.gemini_service import gemini_service
        from bot.ui.embeds import create_resume_job_fit_embed

        async with get_db() as db:
            user = await profile_service.get_profile(db, str(interaction.user.id))
            if not user or not user.resume_file_path:
                await interaction.followup.send(
                    "❌ **Resume Required!** Please upload your resume first using `/profile resume` to evaluate your fit for this job.",
                    ephemeral=True
                )
                return

            resume_text = gemini_service.extract_text_from_file(user.resume_file_path)
            fit_data = await gemini_service.evaluate_resume_fit_for_job(
                resume_text=resume_text,
                target_role=self.job.title,
                job_description=self.job.description,
                company=self.job.company
            )

        embed = create_resume_job_fit_embed(fit_data, user.full_name or user.username)
        await interaction.followup.send(embed=embed, ephemeral=True)
