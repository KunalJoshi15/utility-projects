from __future__ import annotations
import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

def get_utc_date_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

class UserStudyProfile(Base):
    __tablename__ = "user_study_profiles"

    discord_id = Column(String(64), primary_key=True, index=True)
    username = Column(String(100), nullable=True)
    display_name = Column(String(150), nullable=True)
    
    # Gamified Rank & Stats
    rank_level = Column(Integer, default=1)                      # 1 to 7
    rank_title = Column(String(100), default="Novice Scholar")   # "Novice Scholar", "System Architect", etc.
    total_topics_count = Column(Integer, default=0, index=True) # Total unique topics covered
    total_study_minutes = Column(Integer, default=0)
    total_problems_solved = Column(Integer, default=0)
    
    # Custom Reminders & Inactivity Roasts
    reminders_enabled = Column(Boolean, default=True)
    reminder_hour_utc = Column(Integer, default=15)              # 15 UTC = 8:30 PM IST
    target_role = Column(String(150), nullable=True, default="Software Engineer")
    target_companies = Column(String(255), nullable=True, default="Google, Microsoft, Amazon")
    
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    sessions = relationship("DailyStudySession", back_populates="user", cascade="all, delete-orphan", order_by="desc(DailyStudySession.logged_at)")
    topics = relationship("StudyTopicItem", back_populates="user", cascade="all, delete-orphan", order_by="desc(StudyTopicItem.logged_at)")
    badges = relationship("StudyBadge", back_populates="user", cascade="all, delete-orphan")

class DailyStudySession(Base):
    __tablename__ = "daily_study_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), ForeignKey("user_study_profiles.discord_id"), nullable=False, index=True)
    
    session_date = Column(String(20), nullable=False, index=True) # "YYYY-MM-DD"
    duration_minutes = Column(Integer, default=45)
    problems_solved = Column(Integer, default=0)
    category = Column(String(50), default="General")              # DSA, LLD, HLD, Cloud, General
    
    # Notes & Takeaways logged for this session
    notes = Column(Text, nullable=True)
    topics_count = Column(Integer, default=1)
    
    logged_at = Column(DateTime, default=get_utc_now, index=True)

    user = relationship("UserStudyProfile", back_populates="sessions")
    topics = relationship("StudyTopicItem", back_populates="session", cascade="all, delete-orphan")

class StudyTopicItem(Base):
    __tablename__ = "study_topic_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("daily_study_sessions.id"), nullable=True, index=True)
    discord_id = Column(String(64), ForeignKey("user_study_profiles.discord_id"), nullable=False, index=True)
    
    topic_name = Column(String(255), nullable=False, index=True)
    category = Column(String(50), default="General")
    notes = Column(Text, nullable=True)                          # Specific takeaway for this topic
    logged_date = Column(String(20), nullable=False, index=True) # "YYYY-MM-DD"
    logged_at = Column(DateTime, default=get_utc_now, index=True)

    user = relationship("UserStudyProfile", back_populates="topics")
    session = relationship("DailyStudySession", back_populates="topics")

class StudyStreak(Base):
    __tablename__ = "study_streaks"

    discord_id = Column(String(64), primary_key=True, index=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_study_date = Column(String(20), nullable=True)          # "YYYY-MM-DD"
    total_days_studied = Column(Integer, default=0)
    freeze_count = Column(Integer, default=2)

class StudyBadge(Base):
    __tablename__ = "study_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), ForeignKey("user_study_profiles.discord_id"), nullable=False, index=True)
    
    badge_key = Column(String(50), nullable=False)               # e.g. "first_topic", "topic_10", "streak_7"
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    icon = Column(String(20), default="🎖️")
    unlocked_at = Column(DateTime, default=get_utc_now)

    user = relationship("UserStudyProfile", back_populates="badges")

class ActiveLiveSession(Base):
    __tablename__ = "active_live_sessions"

    discord_id = Column(String(64), primary_key=True, index=True)
    guild_id = Column(String(64), nullable=True)
    channel_id = Column(String(64), nullable=True)
    message_id = Column(String(64), nullable=True)               # Active live message to edit
    
    topic_or_goal = Column(String(255), default="General Study")
    category = Column(String(50), default="General")
    
    start_time = Column(DateTime, default=get_utc_now)
    last_heartbeat = Column(DateTime, default=get_utc_now)
