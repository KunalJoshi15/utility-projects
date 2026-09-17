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
from bot.ui.embeds import create_job_embed, create_alert_digest_embed
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
        visa_sponsorship: bool = False,
        delivery_mode: str = "DM",
        frequency_hours: int = 12,
        max_jobs_per_run: int = 3,
        preferred_hour_utc: Optional[int] = None
    ) -> JobAlert:
        """Create a new job alert rule with timing, batch size, and anti-spam delivery preferences."""
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
            visa_sponsorship=visa_sponsorship,
            delivery_mode=delivery_mode.upper() if delivery_mode in ("DM", "CHANNEL") else "DM",
            frequency_hours=max(1, min(168, frequency_hours)),
            max_jobs_per_run=max(1, min(10, max_jobs_per_run)),
            preferred_hour_utc=preferred_hour_utc,
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
        location: Optional[str] = None,
        delivery_mode: str = "DM",
        frequency_hours: int = 12,
        max_jobs_per_run: int = 3
    ) -> List[JobAlert]:
        """Create separate alert monitors for each company configured in the candidate profile."""
        from services.profile_service import profile_service
        user = await profile_service.get_or_create_profile(db, discord_id, "User")
        
        comp_str = companies or user.target_companies or "Google, Microsoft, Amazon, Swiggy, Flipkart"
        comp_list = [c.strip() for c in comp_str.split(",") if c.strip()]
        
        target_role = role or user.current_role or "Software Engineer"
        target_country = country or getattr(user, "country", None) or "India"
        target_loc = location or getattr(user, "city", None) or getattr(user, "location", None) or "Bengaluru"
        
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
                delivery_mode=delivery_mode.upper() if delivery_mode in ("DM", "CHANNEL") else "DM",
                frequency_hours=max(1, min(168, frequency_hours)),
                max_jobs_per_run=max(1, min(10, max_jobs_per_run)),
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(alert)
            created_alerts.append(alert)
            
        await db.commit()
        for a in created_alerts:
            await db.refresh(a)
            
        return created_alerts

    async def update_alert_schedule(
        self,
        db: AsyncSession,
        alert_id: int,
        discord_id: str,
        frequency_hours: Optional[int] = None,
        max_jobs_per_run: Optional[int] = None,
        delivery_mode: Optional[str] = None,
        preferred_hour_utc: Optional[int] = None
    ) -> Optional[JobAlert]:
        """Update the frequency, batch quantity limit, and delivery destination for an alert."""
        result = await db.execute(
            select(JobAlert)
            .where(JobAlert.id == alert_id, JobAlert.discord_id == str(discord_id))
        )
        alert = result.scalars().first()
        if not alert:
            return None

        if frequency_hours is not None:
            alert.frequency_hours = max(1, min(168, frequency_hours))
        if max_jobs_per_run is not None:
            alert.max_jobs_per_run = max(1, min(10, max_jobs_per_run))
        if delivery_mode is not None and delivery_mode.upper() in ("DM", "CHANNEL"):
            alert.delivery_mode = delivery_mode.upper()
        if preferred_hour_utc is not None:
            alert.preferred_hour_utc = max(0, min(23, preferred_hour_utc))

        await db.commit()
        await db.refresh(alert)
        return alert

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

    async def poll_active_alerts_and_notify(self, bot: discord.Client, force_all: bool = False) -> int:
        """Background daemon: checks for new jobs and sends consolidated, anti-spam digests (via DM or Channel)."""
        notifications_sent = 0
        now = datetime.now(timezone.utc)
        try:
            async with get_db() as db:
                result = await db.execute(select(JobAlert).where(JobAlert.is_active == True))
                alerts = list(result.scalars().all())

                for alert in alerts:
                    try:
                        # 1. Timing & Frequency Gate Check (Anti-Spam)
                        if not force_all and alert.last_triggered_at:
                            elapsed_hours = (now - alert.last_triggered_at.replace(tzinfo=timezone.utc) if alert.last_triggered_at.tzinfo is None else (now - alert.last_triggered_at)).total_seconds() / 3600.0
                            required_interval = alert.frequency_hours or 12
                            if elapsed_hours < required_interval:
                                continue  # Wait until next configured trigger cycle

                        # 2. Search matching jobs strictly respecting criteria
                        matching_jobs = await job_service.search_jobs(
                            db=db,
                            query=alert.query,
                            country=alert.country,
                            location=alert.location,
                            company_filter=alert.company,
                            min_salary=alert.min_salary,
                            employment_type=alert.employment_type,
                            visa_sponsorship=bool(alert.visa_sponsorship),
                            limit=12
                        )

                        # 3. Filter out previously notified jobs
                        unseen_jobs = []
                        for job in matching_jobs:
                            seen = await db.execute(
                                select(AlertNotification).where(
                                    AlertNotification.alert_id == alert.id,
                                    AlertNotification.job_id == job.job_id
                                )
                            )
                            if not seen.scalars().first():
                                unseen_jobs.append(job)

                        if not unseen_jobs:
                            alert.last_triggered_at = now
                            await db.commit()
                            continue

                        # 4. Limit to user's configured batch quantity
                        batch_limit = alert.max_jobs_per_run or 3
                        jobs_to_send = unseen_jobs[:batch_limit]

                        # 5. Record notifications in DB
                        for job in jobs_to_send:
                            notif = AlertNotification(
                                alert_id=alert.id,
                                job_id=job.job_id,
                                notified_at=now
                            )
                            db.add(notif)
                        await db.flush()

                        # 6. Format single anti-spam consolidated digest embed
                        digest_embed = create_alert_digest_embed(alert, jobs_to_send)

                        delivered = False
                        # 7a. Deliver via Private DM (Zero public channel spam)
                        if (alert.delivery_mode or "DM").upper() == "DM":
                            try:
                                user = bot.get_user(int(alert.discord_id))
                                if not user:
                                    user = await bot.fetch_user(int(alert.discord_id))
                                if user:
                                    await user.send(embed=digest_embed)
                                    delivered = True
                            except Exception as dm_err:
                                logger.info(f"DM delivery failed for user {alert.discord_id} (DMs closed), falling back to channel: {dm_err}")

                        # 7b. Deliver via Channel (or fallback if DM failed)
                        if not delivered:
                            channel = bot.get_channel(int(alert.channel_id))
                            if not channel:
                                try:
                                    channel = await bot.fetch_channel(int(alert.channel_id))
                                except Exception:
                                    channel = None

                            if channel:
                                await channel.send(
                                    content=f"🔔 <@{alert.discord_id}> **Job Alert Digest:** Found {len(jobs_to_send)} new matching openings:",
                                    embed=digest_embed
                                )
                                delivered = True

                        if delivered:
                            notifications_sent += len(jobs_to_send)
                            alert.last_triggered_at = now
                            await db.commit()

                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"Error processing alert ID {alert.id}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in poll_active_alerts_and_notify: {e}", exc_info=True)

        return notifications_sent

alert_service = AlertService()

