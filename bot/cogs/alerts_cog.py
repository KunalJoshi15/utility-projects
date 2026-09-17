import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing import Optional
from database.db import get_db
from services.alert_service import alert_service
from bot.ui.embeds import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING

class AlertsCog(commands.GroupCog, group_name="alerts"):
    """Commands for setting up automated job alerts and background notifications."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.alert_polling_loop.start()

    def cog_unload(self):
        self.alert_polling_loop.cancel()

    @tasks.loop(minutes=15.0)
    async def alert_polling_loop(self):
        """Periodically scan for new job openings and notify users."""
        await self.bot.wait_until_ready()
        try:
            count = await alert_service.poll_active_alerts_and_notify(self.bot)
            if count > 0:
                print(f"[ALERTS] Dispatched {count} new job alert notifications.")
        except Exception as e:
            print(f"[ALERTS ERROR] Polling error: {e}")

    @app_commands.command(name="create", description="Set up automated job alerts that tag you when matching jobs appear")
    @app_commands.describe(
        query="Target role or tech keywords (e.g. 'Senior Python Engineer', 'Full Stack React', 'Java')",
        country="Target country (India, USA, UK, Canada, Germany, Remote)",
        location="Target city or region (e.g. 'Bengaluru', 'Hyderabad', 'Pune', 'Mumbai', 'Delhi NCR')",
        employment_type="Employment type (Full-time, Internship, Contract, Part-time)",
        min_salary="Minimum target salary / payscale (e.g. '₹ 25 LPA', '₹ 15 LPA', '$150,000')",
        company="Specific target company (optional, e.g. 'Google', 'Amazon', 'Flipkart')",
        visa_sponsorship="Only alert for verified international visa sponsorship & relocation openings"
    )
    @app_commands.choices(
        country=[
            app_commands.Choice(name="🇮🇳 India", value="India"),
            app_commands.Choice(name="🇩🇪 Germany (EU Blue Card)", value="Germany"),
            app_commands.Choice(name="🇳🇱 Netherlands (Highly Skilled Migrant)", value="Netherlands"),
            app_commands.Choice(name="🇬🇧 United Kingdom", value="UK"),
            app_commands.Choice(name="🇨🇦 Canada (Global Talent Stream)", value="Canada"),
            app_commands.Choice(name="🇺🇸 USA (H-1B & L-1 Transfer)", value="USA"),
            app_commands.Choice(name="🌐 Worldwide / Remote", value="Remote"),
        ],
        employment_type=[
            app_commands.Choice(name="Full-time", value="FULLTIME"),
            app_commands.Choice(name="Internship", value="INTERN"),
            app_commands.Choice(name="Contract", value="CONTRACTOR"),
            app_commands.Choice(name="Part-time", value="PARTTIME"),
        ]
    )
    async def create_alert(
        self,
        interaction: discord.Interaction,
        query: str,
        country: Optional[app_commands.Choice[str]] = None,
        location: Optional[str] = None,
        employment_type: Optional[app_commands.Choice[str]] = None,
        min_salary: Optional[str] = None,
        company: Optional[str] = None,
        visa_sponsorship: bool = False
    ):
        await interaction.response.defer(ephemeral=True)

        country_val = country.value if country else "India"
        emp_val = employment_type.value if employment_type else "FULLTIME"

        async with get_db() as db:
            alert = await alert_service.create_alert(
                db=db,
                discord_id=str(interaction.user.id),
                channel_id=str(interaction.channel_id),
                guild_id=str(interaction.guild_id) if interaction.guild_id else None,
                query=query,
                country=country_val,
                location=location,
                company=company,
                employment_type=emp_val,
                min_salary=min_salary,
                visa_sponsorship=visa_sponsorship
            )

        embed = discord.Embed(
            title="🔔 Job Alert Created Successfully!",
            description=f"You will be **tagged in {interaction.channel.mention}** whenever new matching jobs appear across **LinkedIn, Naukri & Career Portals**.",
            color=COLOR_SUCCESS
        )
        embed.add_field(name="Alert ID", value=f"`#{alert.id}`", inline=True)
        embed.add_field(name="🔍 Target Role", value=f"`{alert.query}`", inline=True)
        embed.add_field(name="🌍 Country", value=f"`{alert.country}`", inline=True)
        embed.add_field(name="📍 City / Region", value=f"`{alert.location or 'Any City'}`", inline=True)
        embed.add_field(name="🕒 Employment Type", value=f"`{alert.employment_type}`", inline=True)
        if alert.min_salary:
            embed.add_field(name="💰 Payscale Target", value=f"`{alert.min_salary}`", inline=True)
        if alert.company:
            embed.add_field(name="🏢 Company Filter", value=f"`{alert.company}`", inline=True)
        if alert.visa_sponsorship:
            embed.add_field(name="🛂 Visa Sponsorship", value="`Required (Verified Sponsors Only)`", inline=True)
        embed.add_field(name="⏱️ Polling Frequency", value="`Every 15 minutes` (Run `/alerts check` to test now)", inline=False)

        embed.set_footer(text="Manage alerts anytime with /alerts list or /alerts delete")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="companies", description="Create automatic 15-min vacancy alerts for all your target dream companies")
    @app_commands.describe(
        custom_companies="Optional comma-separated companies (e.g. 'Google, Microsoft, Amazon, Swiggy')",
        role="Target role (optional, defaults to profile role / 'Software Engineer')",
        min_salary="Target minimum paygrade / salary (e.g. '₹ 25 LPA')",
        location="Target city or region (e.g. 'Bengaluru', 'Pune')",
        country="Target country (India, USA, UK, Canada, Germany, Remote)"
    )
    @app_commands.choices(
        country=[
            app_commands.Choice(name="🇮🇳 India", value="India"),
            app_commands.Choice(name="🇺🇸 USA", value="USA"),
            app_commands.Choice(name="🇬🇧 United Kingdom", value="UK"),
            app_commands.Choice(name="🇨🇦 Canada", value="Canada"),
            app_commands.Choice(name="🇩🇪 Germany", value="Germany"),
            app_commands.Choice(name="🌐 Worldwide / Remote", value="Remote"),
        ]
    )
    async def create_company_alerts(
        self,
        interaction: discord.Interaction,
        custom_companies: Optional[str] = None,
        role: Optional[str] = None,
        min_salary: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[app_commands.Choice[str]] = None
    ):
        await interaction.response.defer(ephemeral=True)
        country_val = country.value if country else "India"

        async with get_db() as db:
            alerts = await alert_service.create_company_alerts_for_user(
                db=db,
                discord_id=str(interaction.user.id),
                channel_id=str(interaction.channel_id),
                guild_id=str(interaction.guild_id) if interaction.guild_id else None,
                companies=custom_companies,
                role=role,
                min_salary=min_salary,
                country=country_val,
                location=location
            )

        if not alerts:
            await interaction.followup.send(
                "⚠️ No target companies found. Please set them using `/profile companies names: Google, Microsoft, Amazon` first.",
                ephemeral=True
            )
            return

        company_names = ", ".join([f"`{a.company}`" for a in alerts])
        embed = discord.Embed(
            title=f"🔔 {len(alerts)} Target Company Job Alerts Created!",
            description=f"The bot is now monitoring 24/7 for **{alerts[0].query}** vacancies at:\n{company_names}\n\n"
                        f"Whenever new openings appear in **{location or 'India'}**, you will be **tagged in {interaction.channel.mention}**.",
            color=COLOR_SUCCESS
        )
        if min_salary:
            embed.add_field(name="💰 Target Payscale", value=f"`{min_salary}`", inline=True)
        embed.add_field(name="⏱️ Polling Frequency", value="`Every 15 minutes` (Run `/alerts check` to test now)", inline=True)
        embed.set_footer(text="Manage all alerts with /alerts list or /alerts delete")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="check", description="Manually trigger an immediate scan for your active job alerts")
    async def check_alerts(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        await interaction.followup.send("⏳ Scanning live feeds across LinkedIn, Naukri & Portals for your alerts...", ephemeral=True)
        count = await alert_service.poll_active_alerts_and_notify(self.bot)
        
        await interaction.channel.send(
            f"✅ **Alert Scan Complete:** Dispatched **{count}** new job alert notifications matching active filters!"
        )

    @app_commands.command(name="list", description="View all your active job alert subscriptions")
    async def list_alerts(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            alerts = await alert_service.get_user_alerts(db, str(interaction.user.id))

        if not alerts:
            await interaction.followup.send(
                "ℹ️ You have no active job alerts. Create one using `/alerts create`!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🔔 Your Active Job Alerts ({len(alerts)})",
            description="The bot continuously monitors LinkedIn, Naukri, and career portals for these filters:",
            color=COLOR_PRIMARY
        )

        for alert in alerts:
            details = f"• **Country:** `{alert.country or 'India'}`\n"
            if alert.location:
                details += f"• **City:** `{alert.location}`\n"
            if alert.employment_type:
                details += f"• **Type:** `{alert.employment_type}`\n"
            if alert.min_salary:
                details += f"• **Payscale:** `{alert.min_salary}`\n"
            if alert.company:
                details += f"• **Company:** `{alert.company}`\n"
            details += f"• **Notification Channel:** <#{alert.channel_id}>"

            embed.add_field(
                name=f"Alert #{alert.id}: {alert.query}",
                value=details,
                inline=False
            )

        embed.set_footer(text="To remove an alert, run /alerts delete <alert_id> • Test with /alerts check")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="delete", description="Remove a job alert subscription")
    @app_commands.describe(alert_id="The ID of the alert to delete (find it via /alerts list)")
    async def delete_alert(self, interaction: discord.Interaction, alert_id: int):
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            deleted = await alert_service.delete_alert(db, alert_id, str(interaction.user.id))

        if deleted:
            await interaction.followup.send(f"✅ Alert `#{alert_id}` has been deleted.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Could not find active Alert `#{alert_id}` belonging to you.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AlertsCog(bot))
