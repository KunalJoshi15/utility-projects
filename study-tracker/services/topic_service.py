from __future__ import annotations
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, delete

from database.models import UserStudyProfile, DailyStudySession, StudyTopicItem, StudyStreak, StudyBadge, ActiveLiveSession
from services.gamification_service import gamification_service


logger = logging.getLogger(__name__)

def get_utc_date_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

class TopicService:
    """Core service for multi-topic extraction, session logging, and notes retrieval."""

    def extract_numbered_topics(self, raw_input: str) -> List[str]:
        """
        Parses single or multi-topic inputs into a clean list of topic strings.
        Supports:
        - Numbered inline: '1. Topic A 2. Topic B 3. Topic C'
        - Numbered multiline: '1. Dynamic Programming\n2. Factory Pattern'
        - Bulleted or comma separated: '- Topic A\n- Topic B' or 'Topic A, Topic B'
        """
        if not raw_input or not raw_input.strip():
            return []

        cleaned = raw_input.strip()

        # 1. Numbered items (inline or multiline like "1. A 2. B" or "1) A\n2) B" or "1: A 2: B")
        # Split by start-of-line or whitespace followed by digit(s) and delimiter
        numbered_splits = re.split(r'(?:^|\s+|\n)\d+[\.\)\:\-]\s*', cleaned)
        clean_numbered = [t.strip() for t in numbered_splits if t.strip()]
        if len(clean_numbered) > 1:
            return clean_numbered

        # 2. Check for multiline entries (bullets, dashes, or plain newlines)
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if len(lines) > 1:
            clean_lines = []
            for line in lines:
                sub = re.sub(r'^(?:\d+[\.\)\:\-]?|[\*\-\•\>])\s*', '', line).strip()
                if sub:
                    clean_lines.append(sub)
            if len(clean_lines) > 1:
                return clean_lines

        # 3. Check comma separated if user wrote "Topic A, Topic B, Topic C"
        if "," in cleaned:
            comma_topics = [t.strip() for t in cleaned.split(",") if t.strip()]
            if len(comma_topics) > 1 and all(len(t) < 80 for t in comma_topics):
                return comma_topics

        # 4. Fallback to single topic with leading numbering/bullets stripped
        single = re.sub(r'^(?:\d+[\.\)\:\-]?|[\*\-\•\>])\s*', '', cleaned).strip()
        return [single] if single else []

    async def get_or_create_profile(
        self,
        db: AsyncSession,
        discord_id: str,
        username: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> UserStudyProfile:
        """Fetch or initialize candidate study profile."""
        stmt = select(UserStudyProfile).where(UserStudyProfile.discord_id == discord_id)
        profile = (await db.execute(stmt)).scalar_one_or_none()

        if not profile:
            profile = UserStudyProfile(
                discord_id=discord_id,
                username=username,
                display_name=display_name or username,
                rank_level=0,
                rank_title="Unranked Aspirant",
                total_topics_count=0,
                total_study_minutes=0,
                total_problems_solved=0
            )
            db.add(profile)
            await db.flush()
        else:
            if username and profile.username != username:
                profile.username = username
            if display_name and profile.display_name != display_name:
                profile.display_name = display_name

        return profile

    async def log_study_activity(
        self,
        db: AsyncSession,
        discord_id: str,
        raw_topics: str,
        notes: Optional[str] = None,
        duration_minutes: int = 45,
        problems_solved: int = 0,
        category: str = "General",
        username: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a daily study logging request:
        1. Extracts topics from raw_topics (single or numbered).
        2. Creates DailyStudySession and individual StudyTopicItem records.
        3. Updates user totals & streak.
        4. Checks for Rank level-up and awards Badges.
        """
        extracted_topics = self.extract_numbered_topics(raw_topics)
        if not extracted_topics:
            raise ValueError("No valid topic names found in your input. Please specify what you studied!")

        profile = await self.get_or_create_profile(db, discord_id, username, display_name)
        today_str = get_utc_date_str()

        # 1. Create Daily Study Session
        session = DailyStudySession(
            discord_id=discord_id,
            session_date=today_str,
            duration_minutes=duration_minutes,
            problems_solved=problems_solved,
            category=category,
            notes=notes.strip() if notes else None,
            topics_count=len(extracted_topics)
        )
        db.add(session)
        await db.flush()

        # 2. Add individual topic records
        created_topics = []
        for topic_title in extracted_topics:
            topic_item = StudyTopicItem(
                session_id=session.id,
                discord_id=discord_id,
                topic_name=topic_title[:250],
                category=category,
                notes=notes.strip() if notes else None,
                logged_date=today_str
            )
            db.add(topic_item)
            created_topics.append(topic_item)

        # 3. Update Profile Cumulative Statistics
        prev_level = profile.rank_level
        profile.total_topics_count += len(extracted_topics)
        profile.total_study_minutes += max(0, duration_minutes)
        profile.total_problems_solved += max(0, problems_solved)

        # 4. Update Study Streak
        streak_obj = await self._update_streak(db, discord_id, today_str)

        # 5. Check Rank Promotion
        did_level_up, rank_info = gamification_service.check_rank_promotion(prev_level, profile.total_topics_count)
        profile.rank_level = rank_info["level"]
        profile.rank_title = rank_info["title"]

        # 6. Check and award new milestone badges
        new_badges = await gamification_service.check_and_award_badges(
            db=db,
            discord_id=discord_id,
            total_topics=profile.total_topics_count,
            streak_count=streak_obj.current_streak,
            session_topics_count=len(extracted_topics),
            total_minutes=profile.total_study_minutes
        )

        await db.commit()

        return {
            "session_id": session.id,
            "extracted_topics": extracted_topics,
            "topics_count": len(extracted_topics),
            "notes": notes,
            "duration_minutes": duration_minutes,
            "problems_solved": problems_solved,
            "category": category,
            "streak": streak_obj.current_streak,
            "longest_streak": streak_obj.longest_streak,
            "total_topics": profile.total_topics_count,
            "total_hours": round(profile.total_study_minutes / 60, 1),
            "rank_info": rank_info,
            "did_level_up": did_level_up,
            "new_badges": new_badges
        }

    async def _update_streak(self, db: AsyncSession, discord_id: str, today_str: str) -> StudyStreak:
        """Calculates and updates candidate daily study streak."""
        stmt = select(StudyStreak).where(StudyStreak.discord_id == discord_id)
        streak = (await db.execute(stmt)).scalar_one_or_none()

        if not streak:
            streak = StudyStreak(
                discord_id=discord_id,
                current_streak=1,
                longest_streak=1,
                last_study_date=today_str,
                total_days_studied=1,
                freeze_count=2
            )
            db.add(streak)
            await db.flush()
            return streak

        if streak.last_study_date == today_str:
            # Already studied today, maintain streak
            return streak

        # Calculate difference between today and last study date
        last_dt = datetime.strptime(streak.last_study_date, "%Y-%m-%d").date()
        today_dt = datetime.strptime(today_str, "%Y-%m-%d").date()
        days_diff = (today_dt - last_dt).days

        if days_diff == 1:
            streak.current_streak += 1
        else:
            streak.current_streak = 1 # Streak reset

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.total_days_studied += 1
        streak.last_study_date = today_str
        await db.flush()
        return streak

    async def get_user_notes(
        self,
        db: AsyncSession,
        discord_id: str,
        search_query: Optional[str] = None,
        limit: int = 5,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch past study notes with keyword search and pagination."""
        base_stmt = select(DailyStudySession).where(
            DailyStudySession.discord_id == discord_id,
            DailyStudySession.notes.isnot(None),
            DailyStudySession.notes != ""
        )

        if search_query and search_query.strip():
            q = f"%{search_query.strip()}%"
            base_stmt = base_stmt.where(DailyStudySession.notes.ilike(q))

        # Count total matches
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        # Fetch page items
        page_stmt = base_stmt.order_by(desc(DailyStudySession.logged_at)).limit(limit).offset(offset)
        sessions = list((await db.execute(page_stmt)).scalars().all())

        results = []
        for s in sessions:
            # Fetch topics for this session
            t_stmt = select(StudyTopicItem.topic_name).where(StudyTopicItem.session_id == s.id)
            topics = list((await db.execute(t_stmt)).scalars().all())

            results.append({
                "session_id": s.id,
                "date": s.session_date,
                "category": s.category,
                "duration_minutes": s.duration_minutes,
                "topics": topics,
                "notes": s.notes,
                "logged_at": s.logged_at
            })

        return results, total_count

    async def get_user_topics(
        self,
        db: AsyncSession,
        discord_id: str,
        limit: int = 25,
        offset: int = 0
    ) -> Tuple[List[StudyTopicItem], int]:
        """Fetch all topics covered by a user."""
        stmt = select(StudyTopicItem).where(StudyTopicItem.discord_id == discord_id)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        page_stmt = stmt.order_by(desc(StudyTopicItem.logged_at)).limit(limit).offset(offset)
        topics = list((await db.execute(page_stmt)).scalars().all())
        return topics, total_count

    async def get_user_profile_summary(self, db: AsyncSession, discord_id: str) -> Dict[str, Any]:
        """Get full candidate scorecard, rank, streak, and recent study activity."""
        stmt = select(UserStudyProfile).where(UserStudyProfile.discord_id == discord_id)
        profile = (await db.execute(stmt)).scalar_one_or_none()

        if not profile:
            profile = await self.get_or_create_profile(db, discord_id)

        streak_stmt = select(StudyStreak).where(StudyStreak.discord_id == discord_id)
        streak = (await db.execute(streak_stmt)).scalar_one_or_none()

        rank_info = gamification_service.get_rank_info(profile.total_topics_count)

        badge_stmt = select(StudyBadge).where(StudyBadge.discord_id == discord_id)
        badges = list((await db.execute(badge_stmt)).scalars().all())

        # Recent 3 study sessions
        sess_stmt = select(DailyStudySession).where(DailyStudySession.discord_id == discord_id).order_by(desc(DailyStudySession.logged_at)).limit(3)
        recent_sessions = list((await db.execute(sess_stmt)).scalars().all())

        return {
            "profile": profile,
            "rank_info": rank_info,
            "streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "total_days_studied": streak.total_days_studied if streak else 0,
            "badges": badges,
            "recent_sessions": recent_sessions,
            "total_topics": profile.total_topics_count,
            "total_hours": round(profile.total_study_minutes / 60, 1),
            "total_problems": profile.total_problems_solved
        }

    async def get_session_by_id(
        self,
        db: AsyncSession,
        discord_id: str,
        session_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch a specific study session and its associated topics."""
        stmt = select(DailyStudySession).where(
            DailyStudySession.id == session_id,
            DailyStudySession.discord_id == discord_id
        )
        session = (await db.execute(stmt)).scalar_one_or_none()
        if not session:
            return None

        t_stmt = select(StudyTopicItem).where(StudyTopicItem.session_id == session.id)
        topic_items = list((await db.execute(t_stmt)).scalars().all())
        topics_list = [t.topic_name for t in topic_items]

        return {
            "id": session.id,
            "discord_id": session.discord_id,
            "session_date": session.session_date,
            "duration_minutes": session.duration_minutes,
            "problems_solved": session.problems_solved,
            "category": session.category,
            "notes": session.notes,
            "topics": topics_list,
            "topics_count": len(topics_list),
            "logged_at": session.logged_at
        }

    async def get_user_sessions_paginated(
        self,
        db: AsyncSession,
        discord_id: str,
        limit: int = 5,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch candidate study logs with pagination for the interactive log browser."""
        base_stmt = select(DailyStudySession).where(DailyStudySession.discord_id == discord_id)
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        page_stmt = base_stmt.order_by(desc(DailyStudySession.logged_at)).limit(limit).offset(offset)
        sessions = list((await db.execute(page_stmt)).scalars().all())

        results = []
        for s in sessions:
            t_stmt = select(StudyTopicItem.topic_name).where(StudyTopicItem.session_id == s.id)
            topics = list((await db.execute(t_stmt)).scalars().all())
            results.append({
                "id": s.id,
                "session_date": s.session_date,
                "category": s.category,
                "duration_minutes": s.duration_minutes,
                "problems_solved": s.problems_solved,
                "topics": topics,
                "topics_count": len(topics),
                "notes": s.notes,
                "logged_at": s.logged_at
            })

        return results, total_count

    async def delete_study_session(
        self,
        db: AsyncSession,
        discord_id: str,
        session_id: int
    ) -> Dict[str, Any]:
        """
        Deletes a mistakenly added study session, associated topics, and adjusts profile metrics.
        """
        stmt = select(DailyStudySession).where(
            DailyStudySession.id == session_id,
            DailyStudySession.discord_id == discord_id
        )
        session = (await db.execute(stmt)).scalar_one_or_none()
        if not session:
            raise ValueError(f"Study session #{session_id} was not found or does not belong to you.")

        # Get topics before deletion
        t_stmt = select(StudyTopicItem.topic_name).where(StudyTopicItem.session_id == session.id)
        topics = list((await db.execute(t_stmt)).scalars().all())
        topics_count = len(topics) if topics else session.topics_count
        duration_mins = session.duration_minutes or 0
        problems_count = session.problems_solved or 0

        # Adjust User Profile totals
        prof_stmt = select(UserStudyProfile).where(UserStudyProfile.discord_id == discord_id)
        profile = (await db.execute(prof_stmt)).scalar_one_or_none()

        if profile:
            profile.total_topics_count = max(0, profile.total_topics_count - topics_count)
            profile.total_study_minutes = max(0, profile.total_study_minutes - duration_mins)
            profile.total_problems_solved = max(0, profile.total_problems_solved - problems_count)

            rank_info = gamification_service.get_rank_info(profile.total_topics_count)
            profile.rank_level = rank_info["level"]
            profile.rank_title = rank_info["title"]
        else:
            rank_info = gamification_service.get_rank_info(0)

        # Delete topics and session
        await db.execute(delete(StudyTopicItem).where(StudyTopicItem.session_id == session.id))
        await db.delete(session)
        await db.commit()

        return {
            "session_id": session_id,
            "deleted_topics": topics,
            "deleted_duration": duration_mins,
            "deleted_problems": problems_count,
            "remaining_total_topics": profile.total_topics_count if profile else 0,
            "remaining_total_hours": round((profile.total_study_minutes if profile else 0) / 60, 1),
            "rank_info": rank_info
        }

    async def edit_study_session(
        self,
        db: AsyncSession,
        discord_id: str,
        session_id: int,
        new_raw_topics: Optional[str] = None,
        new_notes: Optional[str] = None,
        new_duration: Optional[int] = None,
        new_problems: Optional[int] = None,
        new_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates an existing study log, re-indexes topic items, and adjusts cumulative metrics.
        """
        stmt = select(DailyStudySession).where(
            DailyStudySession.id == session_id,
            DailyStudySession.discord_id == discord_id
        )
        session = (await db.execute(stmt)).scalar_one_or_none()
        if not session:
            raise ValueError(f"Study session #{session_id} was not found or does not belong to you.")

        prof_stmt = select(UserStudyProfile).where(UserStudyProfile.discord_id == discord_id)
        profile = (await db.execute(prof_stmt)).scalar_one_or_none()
        if not profile:
            profile = await self.get_or_create_profile(db, discord_id)

        # 1. Update topics if provided
        topics_updated = False
        final_topics = []
        if new_raw_topics is not None and new_raw_topics.strip():
            extracted = self.extract_numbered_topics(new_raw_topics)
            if not extracted:
                raise ValueError("No valid topic names found in your updated input.")

            # Get old topic count
            old_topics_stmt = select(StudyTopicItem).where(StudyTopicItem.session_id == session.id)
            old_topics = list((await db.execute(old_topics_stmt)).scalars().all())
            old_count = len(old_topics)
            new_count = len(extracted)

            # Remove old topic items
            await db.execute(delete(StudyTopicItem).where(StudyTopicItem.session_id == session.id))

            # Add new topic items
            for topic_title in extracted:
                item = StudyTopicItem(
                    session_id=session.id,
                    discord_id=discord_id,
                    topic_name=topic_title[:250],
                    category=new_category or session.category or "General",
                    notes=new_notes.strip() if new_notes else session.notes,
                    logged_date=session.session_date
                )
                db.add(item)

            session.topics_count = new_count
            profile.total_topics_count = max(0, profile.total_topics_count - old_count + new_count)
            final_topics = extracted
            topics_updated = True
        else:
            t_stmt = select(StudyTopicItem.topic_name).where(StudyTopicItem.session_id == session.id)
            final_topics = list((await db.execute(t_stmt)).scalars().all())

        # 2. Update Duration
        if new_duration is not None:
            old_dur = session.duration_minutes or 0
            diff_dur = new_duration - old_dur
            profile.total_study_minutes = max(0, profile.total_study_minutes + diff_dur)
            session.duration_minutes = max(0, new_duration)

        # 3. Update Problems Solved
        if new_problems is not None:
            old_prob = session.problems_solved or 0
            diff_prob = new_problems - old_prob
            profile.total_problems_solved = max(0, profile.total_problems_solved + diff_prob)
            session.problems_solved = max(0, new_problems)

        # 4. Update Category
        if new_category is not None and new_category.strip():
            session.category = new_category.strip()

        # 5. Update Notes
        if new_notes is not None:
            session.notes = new_notes.strip() if new_notes.strip() else None

        # Re-evaluate rank
        rank_info = gamification_service.get_rank_info(profile.total_topics_count)
        profile.rank_level = rank_info["level"]
        profile.rank_title = rank_info["title"]

        await db.commit()

        return {
            "session_id": session.id,
            "session_date": session.session_date,
            "topics": final_topics,
            "topics_count": len(final_topics),
            "notes": session.notes,
            "duration_minutes": session.duration_minutes,
            "problems_solved": session.problems_solved,
            "category": session.category,
            "total_topics": profile.total_topics_count,
            "total_hours": round(profile.total_study_minutes / 60, 1),
            "rank_info": rank_info
        }

    async def reset_user_progress(self, db: AsyncSession, discord_id: str) -> bool:
        """
        Completely resets all study progress, streak, topics, sessions, and badges for a candidate.
        """
        # 1. Delete all sessions and cascade topic items
        await db.execute(delete(DailyStudySession).where(DailyStudySession.discord_id == discord_id))
        await db.execute(delete(StudyTopicItem).where(StudyTopicItem.discord_id == discord_id))
        await db.execute(delete(StudyBadge).where(StudyBadge.discord_id == discord_id))
        await db.execute(delete(ActiveLiveSession).where(ActiveLiveSession.discord_id == discord_id))

        # 2. Reset Profile stats
        prof_stmt = select(UserStudyProfile).where(UserStudyProfile.discord_id == discord_id)
        profile = (await db.execute(prof_stmt)).scalar_one_or_none()
        if profile:
            profile.total_topics_count = 0
            profile.total_study_minutes = 0
            profile.total_problems_solved = 0
            profile.rank_level = 0
            profile.rank_title = "Unranked Aspirant"

        # 3. Reset Streak
        streak_stmt = select(StudyStreak).where(StudyStreak.discord_id == discord_id)
        streak = (await db.execute(streak_stmt)).scalar_one_or_none()
        if streak:
            streak.current_streak = 0
            streak.longest_streak = 0
            streak.total_days_studied = 0
            streak.last_study_date = None

        await db.commit()
        logger.info(f"Completely reset study progress for user {discord_id}.")
        return True

    async def get_full_export_data(self, db: AsyncSession, discord_id: str) -> Dict[str, Any]:
        """Collects complete study data payload for Excel export generation."""
        summary = await self.get_user_profile_summary(db, discord_id)
        profile = summary["profile"]
        streak = summary["streak"]

        # Fetch all sessions
        sess_stmt = select(DailyStudySession).where(
            DailyStudySession.discord_id == discord_id
        ).order_by(desc(DailyStudySession.logged_at))
        all_sessions = list((await db.execute(sess_stmt)).scalars().all())

        sessions_data = []
        for s in all_sessions:
            t_stmt = select(StudyTopicItem.topic_name).where(StudyTopicItem.session_id == s.id)
            topics = list((await db.execute(t_stmt)).scalars().all())
            sessions_data.append({
                "id": s.id,
                "session_date": s.session_date,
                "duration_minutes": s.duration_minutes,
                "problems_solved": s.problems_solved,
                "category": s.category,
                "notes": s.notes,
                "topics": topics,
                "logged_at": s.logged_at
            })

        # Fetch all topics
        top_stmt = select(StudyTopicItem).where(
            StudyTopicItem.discord_id == discord_id
        ).order_by(desc(StudyTopicItem.logged_at))
        all_topics = list((await db.execute(top_stmt)).scalars().all())
        topics_data = [{
            "id": t.id,
            "topic_name": t.topic_name,
            "category": t.category,
            "notes": t.notes,
            "logged_date": t.logged_date,
            "logged_at": t.logged_at
        } for t in all_topics]

        # Badges
        badges_data = [{
            "icon": b.icon,
            "title": b.title,
            "description": b.description,
            "unlocked_at": b.unlocked_at
        } for b in summary.get("badges", [])]

        return {
            "discord_id": discord_id,
            "profile": {
                "username": profile.username,
                "display_name": profile.display_name,
                "rank_level": profile.rank_level,
                "rank_title": profile.rank_title,
                "total_topics_count": profile.total_topics_count,
                "total_study_minutes": profile.total_study_minutes,
                "total_problems_solved": profile.total_problems_solved,
                "target_role": profile.target_role,
                "target_companies": profile.target_companies
            },
            "rank_info": summary["rank_info"],
            "streak": {
                "current_streak": summary["streak"],
                "longest_streak": summary["longest_streak"],
                "total_days_studied": summary["total_days_studied"]
            },
            "badges": badges_data,
            "sessions": sessions_data,
            "topics": topics_data
        }

topic_service = TopicService()

