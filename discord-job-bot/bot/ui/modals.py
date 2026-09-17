import discord
from database.db import get_db
from services.profile_service import profile_service
from bot.ui.embeds import create_profile_embed

class ProfileSetupModal(discord.ui.Modal, title="Candidate Profile Setup"):
    def __init__(self, default_name: str = "", discord_user_label: str = ""):
        super().__init__()
        self.full_name = discord.ui.TextInput(
            label="Your Full Name (Mandatory)",
            placeholder="e.g. Jane Doe",
            default=default_name,
            required=True,
            max_length=100
        )
        self.add_item(self.full_name)

        if discord_user_label:
            self.discord_info = discord.ui.TextInput(
                label="Discord User ID (Auto-Populated)",
                default=discord_user_label,
                required=False,
                max_length=100
            )
            self.add_item(self.discord_info)

    async def on_submit(self, interaction: discord.Interaction):
        async with get_db() as db:
            profile = await profile_service.update_profile(
                db=db,
                discord_id=str(interaction.user.id),
                username=interaction.user.name,
                full_name=self.full_name.value.strip()
            )
            embed = create_profile_embed(profile)

        await interaction.response.send_message(
            f"✅ **Profile Configured for {profile.full_name}!**\n"
            f"Your Discord User ID (`{interaction.user.id}`) is linked. Next, upload your resume with `/profile resume`.",
            embed=embed,
            ephemeral=True
        )


class ProfileDetailsModal(discord.ui.Modal, title="Experience & Career Details"):
    current_role = discord.ui.TextInput(
        label="Current / Target Role",
        placeholder="e.g. Senior Backend Engineer",
        required=True,
        max_length=100
    )
    current_company = discord.ui.TextInput(
        label="Current / Previous Company",
        placeholder="e.g. Tech Corp or Freelance",
        required=False,
        max_length=100
    )
    experience_years = discord.ui.TextInput(
        label="Total Years of Experience",
        placeholder="e.g. 4",
        required=True,
        max_length=4
    )
    notice_period = discord.ui.TextInput(
        label="Notice Period (in Days)",
        placeholder="e.g. 30",
        required=False,
        default="30",
        max_length=4
    )
    sponsorship = discord.ui.TextInput(
        label="Requires Visa Sponsorship? (yes/no)",
        placeholder="e.g. no",
        required=False,
        default="no",
        max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            years = int(self.experience_years.value.strip())
        except ValueError:
            years = 0

        try:
            notice = int(self.notice_period.value.strip()) if self.notice_period.value else 30
        except ValueError:
            notice = 30

        sponsorship_required = self.sponsorship.value.strip().lower() in ["yes", "y", "true", "1"]

        async with get_db() as db:
            profile = await profile_service.update_profile(
                db=db,
                discord_id=str(interaction.user.id),
                username=interaction.user.name,
                current_role=self.current_role.value.strip(),
                current_company=self.current_company.value.strip() if self.current_company.value else None,
                years_of_experience=years,
                notice_period_days=notice,
                requires_sponsorship=sponsorship_required
            )
            embed = create_profile_embed(profile)

        await interaction.response.send_message(
            "✅ **Experience Details Updated!**",
            embed=embed,
            ephemeral=True
        )


class LinkedInCookieModal(discord.ui.Modal, title="Save LinkedIn Session Cookie"):
    cookie_value = discord.ui.TextInput(
        label="LinkedIn `li_at` Cookie Value",
        placeholder="Paste your li_at session cookie string here...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        async with get_db() as db:
            await profile_service.save_linkedin_cookie(
                db=db,
                discord_id=str(interaction.user.id),
                li_at_cookie=self.cookie_value.value.strip(),
                username=interaction.user.name
            )
            profile = await profile_service.get_profile(db, str(interaction.user.id))
            embed = create_profile_embed(profile)

        await interaction.response.send_message(
            "🔒 **LinkedIn session cookie encrypted and securely saved.**\n"
            "This will allow the bot to automate LinkedIn Easy Apply without logging in every time.",
            embed=embed,
            ephemeral=True
        )


class JobDescriptionSearchModal(discord.ui.Modal, title="Natural Language Job Search"):
    description = discord.ui.TextInput(
        label="Target Role, Technologies & Responsibilities",
        placeholder="e.g. Looking for a senior role building distributed microservices in Go, Kafka, and Kubernetes...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1500
    )
    preferred_location = discord.ui.TextInput(
        label="Preferred Location / Country (Optional)",
        placeholder="e.g. Bengaluru, Germany, or Remote",
        required=False,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        from services.job_service import job_service
        from bot.ui.embeds import create_job_embed
        from bot.ui.views import JobPaginationView

        full_prompt = self.description.value.strip()
        if self.preferred_location.value:
            full_prompt += f" in {self.preferred_location.value.strip()}"

        async with get_db() as db:
            user = await profile_service.get_profile(db, str(interaction.user.id))
            parsed, jobs = await job_service.search_jobs_by_prompt(
                db=db,
                prompt_text=full_prompt,
                user=user,
                limit=10
            )

        if not jobs:
            await interaction.followup.send(
                f"❌ No matching jobs found for your prompt: *\"{self.description.value[:100]}...\"*. Try modifying the description or keywords.",
                ephemeral=True
            )
            return

        first_job = jobs[0]
        embed = create_job_embed(first_job, 1, len(jobs))
        view = JobPaginationView(jobs=jobs, user_id=str(interaction.user.id))

        tech_list = parsed.get("technologies", [])
        tech_badge = f"**Tech:** `{', '.join(tech_list[:4])}`" if tech_list else ""
        role_badge = f"**Role:** `{parsed.get('primary_role')}`"
        loc_badge = f"**Location:** `{parsed.get('detected_country') or 'Global'}`"
        
        badges = [b for b in [role_badge, tech_badge, loc_badge] if b]

        header = (
            f"🤖 **AI Natural Language Job Search Results**\n"
            f"💡 *\"{parsed.get('summary_intent', full_prompt[:120])}\"*\n"
            f"• " + " • ".join(badges) + f"\n🔍 Found **{len(jobs)}** open listings:"
        )

        await interaction.followup.send(content=header, embed=embed, view=view)


class ResumeJobFitModal(discord.ui.Modal, title="Audit Resume Fit for Job Profile"):
    target_role = discord.ui.TextInput(
        label="Target Role / Job Title",
        placeholder="e.g. Senior Backend Engineer",
        required=True,
        max_length=100
    )
    company_name = discord.ui.TextInput(
        label="Company Name (Optional)",
        placeholder="e.g. Google, Amazon, Uber, Startup",
        required=False,
        max_length=100
    )
    job_description = discord.ui.TextInput(
        label="Job Description & Tech Requirements",
        placeholder="Paste the job description, required tech stack, and key responsibilities here...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
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
                target_role=self.target_role.value.strip(),
                job_description=self.job_description.value.strip(),
                company=self.company_name.value.strip() if self.company_name.value else None
            )

        embed = create_resume_job_fit_embed(fit_data, user.full_name or user.username)
        await interaction.followup.send(embed=embed, ephemeral=True)
