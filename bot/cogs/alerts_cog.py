import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing import Optional
from database.db import get_db
from services.alert_service import alert_service
from bot.ui.embeds import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING

FREQUENCY_CHOICES = [
    app_commands.Choice(name="⚡ Every 1 Hour (Fast Monitor)", value=1),
    app_commands.Choice(name="🕒 Every 3 Hours", value=3),
    app_commands.Choice(name="⏱️ Every 6 Hours", value=6),
    app_commands.Choice(name="🌅 Every 12 Hours (Twice Daily - Default)", value=12),
    app_commands.Choice(name="📅 Every 24 Hours (Daily Digest)", value=24),
]

DELIVERY_CHOICES = [
    app_commands.Choice(name="📬 Private DM (Anti-Spam / Zero Channel Clutter - Recommended)", value="DM"),
    app_commands.Choice(name="📢 Channel Feed (Single Consolidated Embed)", value="CHANNEL"),
]

BATCH_CHOICES = [
    app_commands.Choice(name="1 Job per digest", value=1),
    app_commands.Choice(name="3 Jobs per digest (Recommended)", value=3),
    app_commands.Choice(name="5 Jobs per digest", value=5),
    app_commands.Choice(name="10 Jobs per digest (Maximum)", value=10),
]

class AlertsCog(commands.GroupCog, group_name="alerts"):
    """Commands for setting up automated job alerts and background notifications."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.alert_polling_loop.start()

    def cog_unload(self):
        self.alert_polling_loop.cancel()

    @tasks.loop(minutes=15.0)
    async def alert_polling_loop(self):
        """Periodically scan for new job openings and notify users based on their custom frequency."""
        await self.bot.wait_until_ready()
        try:
            count = await alert_service.poll_active_alerts_and_notify(self.bot, force_all=False)
            if count > 0:
                print(f"[ALERTS] Dispatched {count} new job alert notifications.")
        except Exception as e:
            print(f"[ALERTS ERROR] Polling error: {e}")

    @app_commands.command(name="create", description="Set up automated job alerts with custom timing & anti-spam delivery")
    @app_commands.describe(
        query="Target role or tech keywords (e.g. 'Senior Python Engineer', 'Full Stack React', 'Java')",
        country="Target country (India, USA, UK, Canada, Germany, Remote)",
        location="Target city or region (e.g. 'Bengaluru', 'Hyderabad', 'Pune', 'Mumbai', 'Delhi NCR')",
        employment_type="Employment type (Full-time, Internship, Contract, Part-time)",
        min_salary="Minimum target salary / payscale (e.g. '₹ 25 LPA', '₹ 15 LPA', '$150,000')",
        company="Specific target company (optional, e.g. 'Google', 'Amazon', 'Flipkart')",
        visa_sponsorship="Only alert for verified international visa sponsorship & relocation openings",
        frequency="How often to trigger checks (1h, 3h, 6h, 12h, 24h)",
        max_jobs="Max number of jobs to bundle per alert digest (1-10)",
        delivery="Delivery destination (Private DM to avoid spamming channels, or Channel Feed)"
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
        ],
        frequency=FREQUENCY_CHOICES,
        max_jobs=BATCH_CHOICES,
        delivery=DELIVERY_CHOICES
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
        visa_sponsorship: bool = False,
        frequency: Optional[app_commands.Choice[int]] = None,
        max_jobs: Optional[app_commands.Choice[int]] = None,
        delivery: Optional[app_commands.Choice[str]] = None
    ):
        await interaction.response.defer(ephemeral=True)

        country_val = country.value if country else "India"
        emp_val = employment_type.value if employment_type else "FULLTIME"
        freq_val = frequency.value if frequency else 12
        max_jobs_val = max_jobs.value if max_jobs else 3
        delivery_val = delivery.value if delivery else "DM"

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
                visa_sponsorship=visa_sponsorship,
                delivery_mode=delivery_val,
                frequency_hours=freq_val,
                max_jobs_per_run=max_jobs_val
            )

        embed = discord.Embed(
            title="🔔 Job Alert Created Successfully!",
            description=(
                f"Your customized job monitor for **{alert.query}** is now active.\n"
                f"**Anti-Spam Protected:** Alerts are bundled into a single digest and sent via **{'Private DM 📬' if alert.delivery_mode == 'DM' else f'Channel Feed ({interaction.channel.mention}) 📢'}**."
            ),
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
            
        embed.add_field(name="⏱️ Trigger Frequency", value=f"`Every {alert.frequency_hours} Hours`", inline=True)
        embed.add_field(name="📦 Batch Limit", value=f"`Up to {alert.max_jobs_per_run} jobs per digest`", inline=True)
        embed.add_field(name="📬 Delivery Destination", value=f"`{alert.delivery_mode}` ({'Private DM' if alert.delivery_mode == 'DM' else 'Channel'})", inline=True)

        embed.set_footer(text="Manage alerts with /alerts list, /alerts config, or /alerts delete • Test now with /alerts check")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="companies", description="Create automatic vacancy alerts for all your dream companies with custom timing")
    @app_commands.describe(
        custom_companies="Optional comma-separated companies (e.g. 'Google, Microsoft, Amazon, Swiggy')",
        role="Target role (optional, defaults to profile role / 'Software Engineer')",
        min_salary="Target minimum paygrade / salary (e.g. '₹ 25 LPA')",
        location="Target city or region (e.g. 'Bengaluru', 'Pune')",
        country="Target country (India, USA, UK, Canada, Germany, Remote)",
        frequency="How often to trigger checks (1h, 3h, 6h, 12h, 24h)",
        max_jobs="Max number of jobs to bundle per alert digest (1-10)",
        delivery="Delivery destination (Private DM or Channel Feed)"
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
        frequency=FREQUENCY_CHOICES,
        max_jobs=BATCH_CHOICES,
        delivery=DELIVERY_CHOICES
    )
    async def create_company_alerts(
        self,
        interaction: discord.Interaction,
        custom_companies: Optional[str] = None,
        role: Optional[str] = None,
        min_salary: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[app_commands.Choice[str]] = None,
        frequency: Optional[app_commands.Choice[int]] = None,
        max_jobs: Optional[app_commands.Choice[int]] = None,
        delivery: Optional[app_commands.Choice[str]] = None
    ):
        await interaction.response.defer(ephemeral=True)
        country_val = country.value if country else "India"
        freq_val = frequency.value if frequency else 12
        max_jobs_val = max_jobs.value if max_jobs else 3
        delivery_val = delivery.value if delivery else "DM"

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
                location=location,
                delivery_mode=delivery_val,
                frequency_hours=freq_val,
                max_jobs_per_run=max_jobs_val
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
            description=(
                f"The bot is now monitoring 24/7 for **{alerts[0].query}** vacancies at:\n{company_names}\n\n"
                f"**Anti-Spam Protected:** Delivered via **{'Private DM 📬' if alerts[0].delivery_mode == 'DM' else f'Channel Feed ({interaction.channel.mention}) 📢'}** every **{alerts[0].frequency_hours} hours** (max {alerts[0].max_jobs_per_run} jobs per digest)."
            ),
            color=COLOR_SUCCESS
        )
        if min_salary:
            embed.add_field(name="💰 Target Payscale", value=f"`{min_salary}`", inline=True)
        embed.add_field(name="⏱️ Trigger Frequency", value=f"`Every {alerts[0].frequency_hours} Hours`", inline=True)
        embed.add_field(name="📦 Batch Limit", value=f"`Up to {alerts[0].max_jobs_per_run} jobs`", inline=True)
        embed.set_footer(text="Manage all alerts with /alerts list, /alerts config, or /alerts delete")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="config", description="Customize timing, frequency, batch limits & delivery for an existing alert")
    @app_commands.describe(
        alert_id="The ID of the alert to configure (find it via /alerts list)",
        frequency="How often to trigger checks (1h, 3h, 6h, 12h, 24h)",
        max_jobs="Max number of jobs to bundle per alert digest (1-10)",
        delivery="Delivery destination (Private DM or Channel Feed)"
    )
    @app_commands.choices(
        frequency=FREQUENCY_CHOICES,
        max_jobs=BATCH_CHOICES,
        delivery=DELIVERY_CHOICES
    )
    async def configure_alert(
        self,
        interaction: discord.Interaction,
        alert_id: int,
        frequency: Optional[app_commands.Choice[int]] = None,
        max_jobs: Optional[app_commands.Choice[int]] = None,
        delivery: Optional[app_commands.Choice[str]] = None
    ):
        await interaction.response.defer(ephemeral=True)

        if not frequency and not max_jobs and not delivery:
            await interaction.followup.send(
                "⚠️ Please specify at least one setting to update (`frequency`, `max_jobs`, or `delivery`).",
                ephemeral=True
            )
            return

        async with get_db() as db:
            updated = await alert_service.update_alert_schedule(
                db=db,
                alert_id=alert_id,
                discord_id=str(interaction.user.id),
                frequency_hours=frequency.value if frequency else None,
                max_jobs_per_run=max_jobs.value if max_jobs else None,
                delivery_mode=delivery.value if delivery else None
            )

        if not updated:
            await interaction.followup.send(
                f"❌ Alert `#{alert_id}` was not found under your Discord account.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"⚙️ Alert #{alert_id} Schedule Updated!",
            description=f"Updated timing, limit, and anti-spam delivery settings for **{updated.query}**:",
            color=COLOR_SUCCESS
        )
        embed.add_field(name="⏱️ Frequency", value=f"`Every {updated.frequency_hours} Hours`", inline=True)
        embed.add_field(name="📦 Batch Limit", value=f"`Up to {updated.max_jobs_per_run} jobs per digest`", inline=True)
        embed.add_field(name="📬 Delivery Mode", value=f"`{updated.delivery_mode}` ({'Private DM 📬' if updated.delivery_mode == 'DM' else 'Channel Feed 📢'})", inline=True)
        embed.set_footer(text="Run /alerts list to view all your alerts • Test with /alerts check")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="check", description="Manually trigger an immediate scan for your active job alerts")
    async def check_alerts(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        await interaction.followup.send("⏳ Scanning live feeds across LinkedIn, Naukri & Portals for your alerts...", ephemeral=True)
        count = await alert_service.poll_active_alerts_and_notify(self.bot, force_all=True)
        
        await interaction.followup.send(
            f"✅ **Alert Scan Complete:** Dispatched **{count}** matching job alert digests!",
            ephemeral=True
        )

    @app_commands.command(name="list", description="View all your active job alerts, schedules, and delivery settings")
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
            description="The bot monitors live feeds and delivers anti-spam digests according to your custom schedule:",
            color=COLOR_PRIMARY
        )

        for alert in alerts:
            delivery_desc = "Private DM 📬" if alert.delivery_mode == "DM" else f"Channel <#{alert.channel_id}> 📢"
            details = (
                f"• **Country:** `{alert.country or 'India'}`"
                f"{f' • **City:** `{alert.location}`' if alert.location else ''}\n"
                f"• **Type:** `{alert.employment_type or 'FULLTIME'}`"
                f"{f' • **Payscale:** `{alert.min_salary}`' if alert.min_salary else ''}"
                f"{f' • **Company:** `{alert.company}`' if alert.company else ''}\n"
                f"• **Timing:** `Every {alert.frequency_hours or 12} Hours` • **Limit:** `{alert.max_jobs_per_run or 3} jobs/digest`\n"
                f"• **Delivery:** `{delivery_desc}`"
            )

            embed.add_field(
                name=f"Alert #{alert.id}: {alert.query}",
                value=details,
                inline=False
            )

        embed.set_footer(text="Customize timing: /alerts config <id> • Delete: /alerts delete <id> • Test: /alerts check")
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

