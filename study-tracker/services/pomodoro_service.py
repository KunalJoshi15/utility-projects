import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import PomodoroSession
from services.study_service import study_service

logger = logging.getLogger(__name__)

class PomodoroService:
    def __init__(self):
        # In-memory tracking of active timer sessions: discord_id -> session dict
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    def start_session(
        self,
        discord_id: str,
        task_description: str,
        category: str = "DSA",
        duration_minutes: int = 25
    ) -> Dict[str, Any]:
        """Start a new active Pomodoro study session."""
        session_data = {
            "discord_id": discord_id,
            "task": task_description,
            "category": category.upper(),
            "duration_minutes": duration_minutes,
            "started_at": datetime.now(timezone.utc),
            "status": "RUNNING"
        }
        self._active_sessions[discord_id] = session_data
        return session_data

    def get_active_session(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Fetch active session if any."""
        return self._active_sessions.get(discord_id)

    async def complete_session(self, db: AsyncSession, discord_id: str) -> Optional[Dict[str, Any]]:
        """Mark session as complete and automatically log study time."""
        sess = self._active_sessions.pop(discord_id, None)
        if not sess:
            return None

        # Auto-log into study logs
        await study_service.log_session(
            db=db,
            discord_id=discord_id,
            category=sess["category"],
            topic=sess["task"],
            subtopic_or_problem=f"Pomodoro Focus Session ({sess['duration_minutes']}m)",
            duration_minutes=sess["duration_minutes"],
            problems_solved=1,
            confidence_score=4,
            notes="Completed via Discord Pomodoro Focus Timer"
        )

        # Record in Pomodoro database
        db_sess = PomodoroSession(
            discord_id=discord_id,
            task_description=sess["task"],
            category=sess["category"],
            duration_minutes=sess["duration_minutes"],
            status="COMPLETED",
            started_at=sess["started_at"],
            completed_at=datetime.now(timezone.utc)
        )
        db.add(db_sess)
        await db.commit()

        return sess

    def cancel_session(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Cancel active timer."""
        return self._active_sessions.pop(discord_id, None)

pomodoro_service = PomodoroService()
