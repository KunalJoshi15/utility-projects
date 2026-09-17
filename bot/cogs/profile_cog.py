import discord
from discord import app_commands
from discord.ext import commands
from database.db import get_db
from services.profile_service import profile_service
from services.gemini_service import gemini_service
from bot.ui.embeds import create_profile_embed
from bot.ui.modals import ProfileSetupModal, ProfileDetailsModal, LinkedInCookieModal

class ProfileCog(commands.GroupCog, group_name="profile"):
    """Commands for managing your candidate profile, resume, and credentials."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Open form to configure your contact information and links")
    async def setup_profile(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProfileSetupModal())

    @app_commands.command(name="details", description="Configure work experience, current role, notice period, and sponsorship")
    async def setup_details(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProfileDetailsModal())

    @app_commands.command(name="resume", description="Upload your PDF resume to use for automated job applications & AI review")
    @app_commands.describe(file="Your resume file (PDF format recommended)")
    async def upload_resume(self, interaction: discord.Interaction, file: discord.Attachment):
        if not file.filename.lower().endswith((".pdf", ".docx", ".doc", ".txt")):
            await interaction.response.send_message(
                "❌ Please upload a valid document file (`.pdf`, `.docx`, `.txt`).",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            file_bytes = await file.read()
            async with get_db() as db:
                saved_path = await profile_service.save_resume_file(
                    db=db,
                    discord_id=str(interaction.user.id),
                    filename=file.filename,
                    file_bytes=file_bytes,
                    username=interaction.user.name
                )
                user = await profile_service.get_profile(db, str(interaction.user.id))
                embed = create_profile_embed(user)

            await interaction.followup.send(
                content=f"✅ **Resume '{file.filename}' uploaded and saved successfully!**\n\n"
                        f"👉 **Next Actions You Can Run:**\n"
                        f"• Run `/resume review` for an in-depth **Gemini AI critique & ATS score**\n"
                        f"• Run `/jobs match` to find **LinkedIn & Naukri jobs** matching your resume\n"
                        f"• Run `/resume parse` to auto-fill your candidate profile from the resume",
                embed=embed,
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                content=f"❌ Failed to process resume upload: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="cookie", description="Securely store your LinkedIn session cookie for Easy Apply automation")
    async def setup_cookie(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LinkedInCookieModal())

    @app_commands.command(name="view", description="View your saved candidate profile status")
    async def view_profile(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with get_db() as db:
            user = await profile_service.get_or_create_profile(
                db=db,
                discord_id=str(interaction.user.id),
                username=interaction.user.name
            )
            embed = create_profile_embed(user)
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
