from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import discord
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database.models import ActiveLiveSession, get_utc_now
from database.db import get_db
from services.topic_service import topic_service

logger = logging.getLogger(__name__)

class LiveSessionService:
    """Manages real-time study sessions, manual termination, and offline auto-stop."""

    def __init__(self):
        self._watchdog_task: Optional[asyncio.Task] = None

    def start_watchdog(self, bot: discord.Client):
        """Starts the 60-second presence watchdog background loop."""
        if self._watchdog_task is None or self._watchdog_task.done():
            self._watchdog_task = asyncio.create_task(self._watchdog_loop(bot))
            logger.info("Live Study Session Offline Watchdog started.")

    def stop_watchdog(self):
        """Stops the presence watchdog background loop."""
        if self._watchdog_task and not self._watchdog_task.done():
            self._watchdog_task.cancel()
            logger.info("Live Study Session Offline Watchdog stopped.")

    async def _watchdog_loop(self, bot: discord.Client):
        """Checks every 60s if any user with an active live session has gone offline."""
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await self.check_all_active_sessions(bot)
            except Exception as e:
                logger.error(f"Error in live session watchdog: {e}", exc_info=True)

            await asyncio.sleep(60)

    async def get_active_session(self, db: AsyncSession, discord_id: str) -> Optional[ActiveLiveSession]:
        """Fetch active session for user if one exists."""
        stmt = select(ActiveLiveSession).where(ActiveLiveSession.discord_id == str(discord_id))
        return (await db.execute(stmt)).scalar_one_or_none()

    async def start_live_session(
        self,
        db: AsyncSession,
        discord_id: str,
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        topic_or_goal: str = "General Study",
        category: str = "General"
    ) -> ActiveLiveSession:
        """Start a new active study session for candidate."""
        existing = await self.get_active_session(db, discord_id)
        if existing:
            raise ValueError(f"You already have an active study session started on **{existing.topic_or_goal}**! Use `/session stop` to end it before starting a new one.")

        session = ActiveLiveSession(
            discord_id=str(discord_id),
            guild_id=str(guild_id) if guild_id else None,
            channel_id=str(channel_id) if channel_id else None,
            topic_or_goal=topic_or_goal.strip() or "General Study",
            category=category.strip() or "General",
            start_time=get_utc_now(),
            last_heartbeat=get_utc_now()
        )
        db.add(session)
        await db.commit()
        return session

    async def stop_live_session(
        self,
        db: AsyncSession,
        discord_id: str,
        notes: Optional[str] = None,
        raw_topics: Optional[str] = None,
        problems_solved: int = 0,
        username: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Manually ends active study session and records logged stats."""
        session = await self.get_active_session(db, discord_id)
        if not session:
            raise ValueError("You do not have an active study session running. Start one with `/session start`!")

        now = get_utc_now()
        # Ensure timezone-aware subtraction
        start = session.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        duration_seconds = max(0, (now - start).total_seconds())
        duration_minutes = max(1, int(round(duration_seconds / 60.0)))

        topics_to_log = raw_topics.strip() if raw_topics and raw_topics.strip() else session.topic_or_goal
        session_category = session.category

        # Delete active session from DB
        await db.delete(session)
        await db.flush()

        # Log session into candidate study history
        result = await topic_service.log_study_activity(
            db=db,
            discord_id=str(discord_id),
            raw_topics=topics_to_log,
            notes=notes,
            duration_minutes=duration_minutes,
            problems_solved=problems_solved,
            category=session_category,
            username=username,
            display_name=display_name
        )

        result["live_duration_minutes"] = duration_minutes
        result["live_duration_seconds"] = int(duration_seconds)
        result["started_at"] = start
        result["ended_at"] = now
        return result

    async def auto_stop_offline_session(
        self,
        bot: discord.Client,
        db: AsyncSession,
        session: ActiveLiveSession,
        reason: str = "User went Offline"
    ) -> Optional[Dict[str, Any]]:
        """Automatically stops session when user disconnects or goes offline."""
        discord_id = session.discord_id
        now = get_utc_now()
        start = session.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        duration_seconds = max(0, (now - start).total_seconds())
        duration_minutes = max(1, int(round(duration_seconds / 60.0)))

        topic_str = session.topic_or_goal
        category = session.category
        channel_id = session.channel_id

        # Delete active session
        await db.delete(session)
        await db.flush()

        # Log the session
        result = await topic_service.log_study_activity(
            db=db,
            discord_id=discord_id,
            raw_topics=topic_str,
            notes=f"Auto-saved live session ({reason}).",
            duration_minutes=duration_minutes,
            problems_solved=0,
            category=category
        )

        logger.info(f"Auto-stopped live session for user {discord_id} ({duration_minutes} mins). Reason: {reason}")

        # Notify user via DM or channel
        try:
            user = await bot.fetch_user(int(discord_id))
            if user:
                embed = discord.Embed(
                    title="⏹️ Live Study Session Auto-Concluded",
                    description=(
                        f"Hey **{user.display_name}**! Your active live study session on **{topic_str}** was automatically saved because **you went offline on Discord**.\n\n"
                        f"• ⏱️ **Active Time Logged:** `{duration_minutes} Minutes`\n"
                        f"• 🔥 **Updated Streak:** `{result.get('streak', 1)} Days`\n"
                        f"• 📚 **Total Topics Mastered:** `{result.get('total_topics', 1)}`"
                    ),
                    color=0x2ECC71 # Green
                )
                embed.set_footer(text="Your study progress is always safe • Resume anytime with /session start")
                await user.send(embed=embed)
        except Exception as e:
            logger.debug(f"Could not send DM to {discord_id}: {e}")

        return result

    async def check_all_active_sessions(self, bot: discord.Client):
        """Watchdog routine checking if active session users are offline."""
        async with get_db() as db:
            stmt = select(ActiveLiveSession)
            active_sessions = list((await db.execute(stmt)).scalars().all())

            for sess in active_sessions:
                user_id = int(sess.discord_id)
                
                # Check status across bot guilds
                is_online = False
                for guild in bot.guilds:
                    member = guild.get_member(user_id)
                    if member and member.status != discord.Status.offline:
                        is_online = True
                        break

                if not is_online:
                    # User is offline in all guilds!
                    await self.auto_stop_offline_session(
                        bot=bot,
                        db=db,
                        session=sess,
                        reason="Detected Discord Offline Status"
                    )

live_session_service = LiveSessionService()
