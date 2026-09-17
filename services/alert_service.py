import logging
import asyncio
import discord
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.models import JobAlert, AlertNotification, CachedJob, UserProfile
from services.job_service import job_service
from bot.ui.embeds import create_job_embed
from bot.ui.views import JobDetailView

logger = logging.getLogger(__name__)

class AlertService:
    async def create_alert(
        self,
        db: AsyncSession,
        discord_id: str,
        channel_id: str,
        guild_id: Optional[str],
        query: str,
        country: Optional[str] = "India",
        location: Optional[str] = None,
        company: Optional[str] = None,
        employment_type: Optional[str] = "FULLTIME",
        min_salary: Optional[str] = None,
    ) -> JobAlert:
        """Create a new job alert rule for a user."""
        from services.profile_service import profile_service
        await profile_service.get_or_create_profile(db, discord_id, "User")

        alert = JobAlert(
            discord_id=str(discord_id),
            guild_id=str(guild_id) if guild_id else None,
            channel_id=str(channel_id),
            query=query.strip(),
            country=country.strip() if country else "India",
            location=location.strip() if location else None,
            company=company.strip() if company else None,
            employment_type=employment_type.strip() if employment_type else "FULLTIME",
            min_salary=min_salary.strip() if min_salary else None,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert

    async def create_company_alerts_for_user(
        self,
        db: AsyncSession,
        discord_id: str,
        channel_id: str,
        guild_id: Optional[str] = None,
        companies: Optional[str] = None,
        role: Optional[str] = None,
        min_salary: Optional[str] = None,
        country: Optional[str] = "India",
        location: Optional[str] = None
    ) -> List[JobAlert]:
        """Create separate alert monitors for each company configured in the candidate profile."""
        from services.profile_service import profile_service
        user = await profile_service.get_or_create_profile(db, discord_id, "User")
        
        comp_str = companies or user.target_companies or "Google, Microsoft, Amazon, Swiggy, Flipkart"
        comp_list = [c.strip() for c in comp_str.split(",") if c.strip()]
        
        target_role = role or user.current_role or "Software Engineer"
        target_country = country or user.country or "India"
        target_loc = location or user.city or "Bengaluru"
        
        created_alerts = []
        for comp in comp_list:
            alert = JobAlert(
                discord_id=str(discord_id),
                guild_id=str(guild_id) if guild_id else None,
                channel_id=str(channel_id),
                query=target_role,
                country=target_country,
                location=target_loc,
                company=comp,
                employment_type="FULLTIME",
                min_salary=min_salary,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(alert)
            created_alerts.append(alert)
            
        await db.commit()
        for a in created_alerts:
            await db.refresh(a)
            
        return created_alerts

    async def get_user_alerts(self, db: AsyncSession, discord_id: str) -> List[JobAlert]:
        """Fetch all alerts configured by a specific user."""
        result = await db.execute(
            select(JobAlert)
            .where(JobAlert.discord_id == str(discord_id))
            .order_by(JobAlert.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_alert(self, db: AsyncSession, alert_id: int, discord_id: str) -> bool:
        """Delete an alert rule."""
        result = await db.execute(
            select(JobAlert)
            .where(JobAlert.id == alert_id, JobAlert.discord_id == str(discord_id))
        )
        alert = result.scalars().first()
        if alert:
            await db.delete(alert)
            await db.commit()
            return True
        return False

    async def poll_active_alerts_and_notify(self, bot: discord.Client) -> int:
        """Background daemon: checks for new jobs and pings users in their Discord channels."""
        notifications_sent = 0
        try:
            async with get_db() as db:
                result = await db.execute(select(JobAlert).where(JobAlert.is_active == True))
                alerts = list(result.scalars().all())

                for alert in alerts:
                    try:
                        channel = bot.get_channel(int(alert.channel_id))
                        if not channel:
                            try:
                                channel = await bot.fetch_channel(int(alert.channel_id))
                            except Exception:
                                channel = None

                        if not channel:
                            continue

                        # Search matching jobs strictly respecting country, location, employment_type, and salary
                        matching_jobs = await job_service.search_jobs(
                            db=db,
                            query=alert.query,
                            country=alert.country,
                            location=alert.location,
                            company_filter=alert.company,
                            min_salary=alert.min_salary,
                            employment_type=alert.employment_type,
                            limit=4
                        )

                        for job in matching_jobs:
                            # Check if already notified
                            seen = await db.execute(
                                select(AlertNotification).where(
                                    AlertNotification.alert_id == alert.id,
                                    AlertNotification.job_id == job.job_id
                                )
                            )
                            if seen.scalars().first():
                                continue  # Skip already sent jobs

                            # Record notification
                            notif = AlertNotification(
                                alert_id=alert.id,
                                job_id=job.job_id,
                                notified_at=datetime.now(timezone.utc)
                            )
                            db.add(notif)
                            await db.flush()

                            # Send Discord notification tagging the user
                            embed = create_job_embed(job, 1, 1)
                            view = JobDetailView(job=job, user_id=alert.discord_id)
                            
                            criteria_text = f"**Role:** `{alert.query}` • **Country:** `{alert.country or 'India'}`"
                            if alert.location:
                                criteria_text += f" • **City:** `{alert.location}`"
                            if alert.company:
                                criteria_text += f" • **Company:** `{alert.company}`"
                            if alert.min_salary:
                                criteria_text += f" • **Salary:** `{alert.min_salary}`"
                            if alert.employment_type:
                                criteria_text += f" • **Type:** `{alert.employment_type}`"

                            await channel.send(
                                content=f"🔔 <@{alert.discord_id}> **New Job Alert!** Found a matching opening ({criteria_text}):",
                                embed=embed,
                                view=view
                            )
                            notifications_sent += 1
                            await asyncio.sleep(1)

                        await db.commit()

                    except Exception as e:
                        logger.error(f"Error processing alert ID {alert.id}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in poll_active_alerts_and_notify: {e}", exc_info=True)

        return notifications_sent

alert_service = AlertService()
