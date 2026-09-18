from __future__ import annotations
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.db import get_db
from database.models import UserStudyProfile, StudyStreak, DailyStudySession
from services.roast_service import roast_service

logger = logging.getLogger(__name__)

class ReminderService:
    """Background service to detect inactive candidates and send daily sarcastic roasts / reminders."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._sent_today_cache: Dict[str, str] = {}  # {discord_id: "YYYY-MM-DD"}

    def start(self, bot: discord.Client):
        """Start the background reminder loop."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._reminder_loop(bot))
            logger.info("Daily Inactivity Sarcastic Roast Service started.")

    def stop(self):
        """Stop the background reminder loop."""
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Daily Inactivity Sarcastic Roast Service stopped.")

    async def _reminder_loop(self, bot: discord.Client):
        """Loop running every 30 minutes to check if users need a roast wakeup."""
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await self.check_and_send_roasts(bot)
            except Exception as e:
                logger.error(f"Error in inactivity roast loop: {e}", exc_info=True)

            # Check every 30 minutes
            await asyncio.sleep(1800)

    async def check_and_send_roasts(self, bot: discord.Client) -> int:
        """Find candidates who have not logged anything today and deliver a sarcastic roast."""
        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")
        current_hour_utc = now_utc.hour

        sent_count = 0
        async with get_db() as db:
            stmt = select(UserStudyProfile).where(UserStudyProfile.reminders_enabled == True)
            profiles = list((await db.execute(stmt)).scalars().all())

            for prof in profiles:
                # Check if already notified today
                if self._sent_today_cache.get(prof.discord_id) == today_str:
                    continue

                # Check configured reminder hour (default 15 UTC = 8:30 PM IST)
                target_hour = prof.reminder_hour_utc if prof.reminder_hour_utc is not None else 15
                if current_hour_utc < target_hour:
                    continue

                # Check if user logged any session today
                sess_stmt = select(DailyStudySession).where(
                    DailyStudySession.discord_id == prof.discord_id,
                    DailyStudySession.session_date == today_str
                )
                today_sess = (await db.execute(sess_stmt)).scalar_one_or_none()
                if today_sess:
                    continue # Studied today! Good job!

                # Get streak
                streak_stmt = select(StudyStreak).where(StudyStreak.discord_id == prof.discord_id)
                streak = (await db.execute(streak_stmt)).scalar_one_or_none()
                streak_count = streak.current_streak if streak else 0

                # Deliver roast DM!
                success = await self._send_roast_dm(bot, prof, streak_count)
                if success:
                    self._sent_today_cache[prof.discord_id] = today_str
                    sent_count += 1

        if sent_count > 0:
            logger.info(f"Delivered {sent_count} daily sarcastic roasts to inactive candidates.")
        return sent_count

    async def _send_roast_dm(self, bot: discord.Client, profile: UserStudyProfile, streak_count: int) -> bool:
        """Send sarcastic motivational DM roast to the slacking candidate."""
        try:
            user = await bot.fetch_user(int(profile.discord_id))
            if not user:
                return False

            roast_msg = roast_service.get_random_roast(
                username=profile.display_name or profile.username or user.name,
                streak_count=streak_count
            )

            embed = discord.Embed(
                title="🚨 Daily Study Inactivity Alert: Slacker Detected! 🚨",
                description=roast_msg,
                color=0xFF4757 # Crimson red
            )
            embed.add_field(
                name="⚡ How to save your streak & silence the roast:",
                value="Run `/study log <topics>` or `/study quicklog` now to log what you studied today!",
                inline=False
            )
            embed.set_footer(text="Consistency beats talent • Powered by Study Tracker Bot")

            await user.send(embed=embed)
            return True
        except Exception as e:
            logger.warning(f"Could not send roast DM to user {profile.discord_id}: {e}")
            return False

reminder_service = ReminderService()
