import discord
from database.db import get_db
from services.profile_service import profile_service
from bot.ui.embeds import create_profile_embed

class ProfileSetupModal(discord.ui.Modal, title="Candidate Profile Setup"):
    full_name = discord.ui.TextInput(
        label="Full Name",
        placeholder="e.g. Jane Doe",
        required=True,
        max_length=100
    )
    email = discord.ui.TextInput(
        label="Email Address",
        placeholder="e.g. jane.doe@example.com",
        required=True,
        max_length=100
    )
    phone = discord.ui.TextInput(
        label="Phone Number (with Country Code)",
        placeholder="e.g. +1 555-0199 or +91 9876543210",
        required=True,
        max_length=30
    )
    location = discord.ui.TextInput(
        label="Location (City, Country)",
        placeholder="e.g. San Francisco, USA or Bangalore, India",
        required=True,
        max_length=100
    )
    linkedin_url = discord.ui.TextInput(
        label="LinkedIn Profile URL",
        placeholder="e.g. https://www.linkedin.com/in/janedoe",
        required=False,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        city = self.location.value.split(",")[0].strip() if "," in self.location.value else self.location.value.strip()
        country = self.location.value.split(",")[1].strip() if "," in self.location.value else "Global"

        async with get_db() as db:
            profile = await profile_service.update_profile(
                db=db,
                discord_id=str(interaction.user.id),
                username=interaction.user.name,
                full_name=self.full_name.value.strip(),
                email=self.email.value.strip(),
                phone=self.phone.value.strip(),
                city=city,
                country=country,
                linkedin_url=self.linkedin_url.value.strip() if self.linkedin_url.value else None
            )
            embed = create_profile_embed(profile)

        await interaction.response.send_message(
            "✅ **Profile Updated!** Don't forget to attach your resume using `/profile resume`.",
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
