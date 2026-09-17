import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.db import get_db
from database.models import UserStudyProfile, StudyLog, StudyStreak
from services.study_service import study_service

logger = logging.getLogger(__name__)

class ReminderService:
    """Background service to send daily inactivity reminders to candidates."""

    def __init__(self):
        self._task: asyncio.Task = None
        self._sent_today_cache = {}  # {discord_id: "YYYY-MM-DD"}

    def start(self, bot: discord.Client):
        """Start the background reminder loop."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._reminder_loop(bot))
            logger.info("Daily Inactivity Reminder Service started.")

    def stop(self):
        """Stop the background reminder loop."""
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Daily Inactivity Reminder Service stopped.")

    async def _reminder_loop(self, bot: discord.Client):
        """Loop running every 30 minutes to check if reminders are due."""
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await self.check_and_send_reminders(bot)
            except Exception as e:
                logger.error(f"Error in reminder loop: {e}", exc_info=True)

            # Wait 30 minutes before next check
            await asyncio.sleep(1800)

    async def check_and_send_reminders(self, bot: discord.Client) -> int:
        """Find candidates who have not studied today and send gentle DM reminders."""
        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")
        current_hour_utc = now_utc.hour

        sent_count = 0
        async with get_db() as db:
            stmt = select(UserStudyProfile).where(UserStudyProfile.reminders_enabled == True)
            profiles = list((await db.execute(stmt)).scalars().all())

            for prof in profiles:
                # Check if already sent today
                if self._sent_today_cache.get(prof.discord_id) == today_str:
                    continue

                # Check if current UTC hour matches configured reminder hour
                target_hour = prof.reminder_hour_utc if prof.reminder_hour_utc is not None else 15
                if current_hour_utc < target_hour:
                    continue

                # Check streak status / if studied today
                streak_data = await study_service.get_streak_status(db, prof.discord_id)
                if streak_data.get("studied_today"):
                    continue

                # User has not studied today and reminder hour is reached!
                success = await self._send_reminder_dm(bot, prof, streak_data)
                if success:
                    self._sent_today_cache[prof.discord_id] = today_str
                    sent_count += 1

        if sent_count > 0:
            logger.info(f"Delivered {sent_count} daily study reminders to candidates.")
        return sent_count

    async def _send_reminder_dm(self, bot: discord.Client, profile: UserStudyProfile, streak: Dict[str, Any]) -> bool:
        """Send motivational DM reminder to the candidate."""
        try:
            user = await bot.fetch_user(int(profile.discord_id))
            if not user:
                return False

            streak_count = streak.get("current_streak", 0)
            streak_text = f"🔥 **{streak_count}-Day Streak** at risk!" if streak_count > 0 else "⚡ Start a fresh streak today!"
            exit_text = f"🎯 **Target Exit Date:** `{profile.target_exit_date}`\n" if profile.target_exit_date else ""

            embed = discord.Embed(
                title="⏰ Daily Study & Preparation Reminder",
                description=(
                    f"Hey **{profile.display_name or profile.username or 'Candidate'}**! 👋\n\n"
                    f"You haven't logged a study session for today yet.\n"
                    f"{exit_text}"
                    f"**Current Status:** {streak_text}\n\n"
                    f"Consistency is the key to landing your target role at `{profile.target_companies or 'your dream companies'}`!\n\n"
                    f"💡 **Quick Actions:**\n"
                    f"• `/study quicklog` - Quick 30-second session log\n"
                    f"• `/study pomodoro` - 25-minute focus study block\n"
                    f"• `/study quiz` - Quick 5-minute technical quiz\n"
                    f"• `/study schedule` - View today's planned topics"
                ),
                color=0xFEE75C  # Warning Yellow
            )
            embed.set_footer(text="Keep the momentum going! • Disable anytime with /study reminders")

            await user.send(embed=embed)
            return True
        except discord.Forbidden:
            logger.debug(f"Cannot DM user {profile.discord_id} (DMs closed)")
            return False
        except Exception as e:
            logger.warning(f"Failed to send reminder DM to {profile.discord_id}: {e}")
            return False

reminder_service = ReminderService()
