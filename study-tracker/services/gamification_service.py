from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from database.models import UserStudyProfile, StudyStreak, StudyBadge, DailyStudySession, StudyTopicItem

# Rank Hierarchy: (Min Topics, Level, Title, Icon, Next Target)
RANKS = [
    (500, 7, "Grandmaster Legend", "🌟", None),
    (250, 6, "Principal Champion", "👑", 500),
    (100, 5, "System Architect", "🔮", 250),
    (50, 4, "Design Artisan", "🎖️", 100),
    (25, 3, "Algorithm Specialist", "🥇", 50),
    (10, 2, "Code Apprentice", "🥈", 25),
    (1, 1, "Novice Scholar", "🥉", 10),
    (0, 0, "Unranked Aspirant", "🌱", 1)
]

BADGE_DEFINITIONS = {
    "first_topic": ("First Step 🎯", "Logged your very first study topic!", "🎯"),
    "multi_topic_3": ("Triple Threat ⚡", "Logged 3 or more topics in a single study session!", "⚡"),
    "multi_topic_5": ("Knowledge Blitz 🌪️", "Logged 5 or more topics in a single day!", "🌪️"),
    "topic_10": ("Double Digits 🔟", "Covered 10 distinct technical topics!", "🔟"),
    "topic_25": ("Quarter Century 🥉", "Covered 25 technical topics!", "🥉"),
    "topic_50": ("Half-Century Scholar 🥈", "Covered 50 technical topics!", "🥈"),
    "topic_100": ("Century Club 🥇", "Mastered 100 technical topics!", "🥇"),
    "streak_3": ("Ignition 🔥", "Maintained a 3-day active study streak!", "🔥"),
    "streak_7": ("Unstoppable Week 🚀", "Maintained a 7-day study streak!", "🚀"),
    "streak_14": ("Fortnight Champion 🛡️", "Maintained a 14-day study streak!", "🛡️"),
    "streak_30": ("Habit Master 💎", "Maintained a 30-day uninterrupted study streak!", "💎"),
    "study_10_hours": ("Dedicated Scholar ⏱️", "Logged over 10 hours of active study time!", "⏱️"),
    "study_50_hours": ("Deep Work Master 🧘", "Logged over 50 hours of active study time!", "🧘"),
}

class GamificationService:
    """Manages candidate rank progression, badges, and server leaderboards."""

    def get_rank_info(self, total_topics: int) -> Dict[str, Any]:
        """Calculates current rank tier, title, icon, and progress towards next rank."""
        for min_topics, level, title, icon, next_target in RANKS:
            if total_topics >= min_topics:
                if next_target is not None:
                    needed = next_target - min_topics
                    completed = total_topics - min_topics
                    pct = min(100, int((completed / needed) * 100)) if needed > 0 else 100
                    topics_left = next_target - total_topics
                else:
                    pct = 100
                    topics_left = 0

                return {
                    "level": level,
                    "title": title,
                    "icon": icon,
                    "total_topics": total_topics,
                    "next_target": next_target,
                    "topics_left": topics_left,
                    "progress_pct": pct
                }

        return {
            "level": 0,
            "title": "Unranked Aspirant",
            "icon": "🌱",
            "total_topics": total_topics,
            "next_target": 1,
            "topics_left": 1,
            "progress_pct": 0
        }

    def check_rank_promotion(self, previous_level: int, current_topics: int) -> Tuple[bool, Dict[str, Any]]:
        """Checks if a user leveled up after adding new topics."""
        rank_info = self.get_rank_info(current_topics)
        did_level_up = rank_info["level"] > previous_level and rank_info["level"] > 0
        return did_level_up, rank_info

    async def check_and_award_badges(
        self,
        db: AsyncSession,
        discord_id: str,
        total_topics: int,
        streak_count: int,
        session_topics_count: int,
        total_minutes: int
    ) -> List[StudyBadge]:
        """Awards new milestone badges to candidate if unlocked."""
        # Get existing badges
        stmt = select(StudyBadge.badge_key).where(StudyBadge.discord_id == discord_id)
        existing_keys = set((await db.execute(stmt)).scalars().all())

        new_badges = []

        def _award(key: str):
            if key in BADGE_DEFINITIONS and key not in existing_keys:
                title, desc, icon = BADGE_DEFINITIONS[key]
                b = StudyBadge(
                    discord_id=discord_id,
                    badge_key=key,
                    title=title,
                    description=desc,
                    icon=icon
                )
                db.add(b)
                new_badges.append(b)
                existing_keys.add(key)

        # Topic Badges
        if total_topics >= 1:
            _award("first_topic")
        if total_topics >= 10:
            _award("topic_10")
        if total_topics >= 25:
            _award("topic_25")
        if total_topics >= 50:
            _award("topic_50")
        if total_topics >= 100:
            _award("topic_100")

        # Session Topics
        if session_topics_count >= 3:
            _award("multi_topic_3")
        if session_topics_count >= 5:
            _award("multi_topic_5")

        # Streak Badges
        if streak_count >= 3:
            _award("streak_3")
        if streak_count >= 7:
            _award("streak_7")
        if streak_count >= 14:
            _award("streak_14")
        if streak_count >= 30:
            _award("streak_30")

        # Study Hours
        if total_minutes >= 600:
            _award("study_10_hours")
        if total_minutes >= 3000:
            _award("study_50_hours")

        if new_badges:
            await db.commit()

        return new_badges

    async def get_leaderboard(self, db: AsyncSession, sort_by: str = "topics", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch server leaderboard ranked by topics, streak, or hours."""
        if sort_by == "streak":
            stmt = (
                select(StudyStreak, UserStudyProfile)
                .join(UserStudyProfile, StudyStreak.discord_id == UserStudyProfile.discord_id)
                .order_by(desc(StudyStreak.current_streak), desc(StudyStreak.total_days_studied))
                .limit(limit)
            )
            rows = (await db.execute(stmt)).all()
            leaderboard = []
            for streak, prof in rows:
                rank_info = self.get_rank_info(prof.total_topics_count)
                leaderboard.append({
                    "discord_id": prof.discord_id,
                    "username": prof.display_name or prof.username or f"User {prof.discord_id[:4]}",
                    "value_primary": f"{streak.current_streak} Days",
                    "value_secondary": f"Best: {streak.longest_streak}d • Total: {streak.total_days_studied}d",
                    "rank_title": rank_info["title"],
                    "rank_icon": rank_info["icon"],
                    "total_topics": prof.total_topics_count,
                    "study_hours": round(prof.total_study_minutes / 60, 1)
                })
            return leaderboard

        elif sort_by == "hours":
            stmt = (
                select(UserStudyProfile)
                .order_by(desc(UserStudyProfile.total_study_minutes), desc(UserStudyProfile.total_topics_count))
                .limit(limit)
            )
            profiles = list((await db.execute(stmt)).scalars().all())
            leaderboard = []
            for prof in profiles:
                rank_info = self.get_rank_info(prof.total_topics_count)
                hours = round(prof.total_study_minutes / 60, 1)
                leaderboard.append({
                    "discord_id": prof.discord_id,
                    "username": prof.display_name or prof.username or f"User {prof.discord_id[:4]}",
                    "value_primary": f"{hours} Hours",
                    "value_secondary": f"{prof.total_topics_count} topics • {prof.total_problems_solved} problems",
                    "rank_title": rank_info["title"],
                    "rank_icon": rank_info["icon"],
                    "total_topics": prof.total_topics_count,
                    "study_hours": hours
                })
            return leaderboard

        else: # Default: topics
            stmt = (
                select(UserStudyProfile)
                .order_by(desc(UserStudyProfile.total_topics_count), desc(UserStudyProfile.total_study_minutes))
                .limit(limit)
            )
            profiles = list((await db.execute(stmt)).scalars().all())
            leaderboard = []
            for prof in profiles:
                rank_info = self.get_rank_info(prof.total_topics_count)
                leaderboard.append({
                    "discord_id": prof.discord_id,
                    "username": prof.display_name or prof.username or f"User {prof.discord_id[:4]}",
                    "value_primary": f"{prof.total_topics_count} Topics",
                    "value_secondary": f"{round(prof.total_study_minutes / 60, 1)}h studied • Level {rank_info['level']}",
                    "rank_title": rank_info["title"],
                    "rank_icon": rank_info["icon"],
                    "total_topics": prof.total_topics_count,
                    "study_hours": round(prof.total_study_minutes / 60, 1)
                })
            return leaderboard

gamification_service = GamificationService()
