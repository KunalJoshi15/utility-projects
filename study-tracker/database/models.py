import enum
from datetime import datetime, timezone
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

class StudyCategory(enum.Enum):
    DSA = "DSA"
    LLD = "LLD"
    HLD = "HLD"
    MICROSERVICES = "MICROSERVICES"
    DEVOPS_CLOUD = "DEVOPS_CLOUD"
    CORE_CS = "CORE_CS"
    MOCK_INTERVIEW = "MOCK_INTERVIEW"
    CUSTOM = "CUSTOM"

class UserStudyProfile(Base):
    __tablename__ = "user_study_profiles"

    discord_id = Column(String(64), primary_key=True, index=True)
    username = Column(String(100), nullable=True)
    display_name = Column(String(150), nullable=True)
    
    target_role = Column(String(150), nullable=True, default="Software Engineer")
    target_companies = Column(String(255), nullable=True, default="Google, Microsoft, Amazon")
    target_interview_date = Column(String(50), nullable=True)
    target_exit_date = Column(String(50), nullable=True)          # e.g. "2026-12-31" or "3 Months"
    daily_study_slots = Column(String(255), nullable=True, default="Morning 7:30-9:00 AM, Evening 8:30-10:00 PM")
    reminders_enabled = Column(Boolean, default=True)
    reminder_hour_utc = Column(Integer, default=15)               # 15 UTC = 8:30 PM IST
    daily_goal_minutes = Column(Integer, default=120)
    daily_goal_problems = Column(Integer, default=3)
    
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    logs = relationship("StudyLog", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("StudyGoal", back_populates="user", cascade="all, delete-orphan")
    topics = relationship("RoadmapTopicItem", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("StudySchedulePlan", back_populates="user", cascade="all, delete-orphan")

class StudyLog(Base):
    __tablename__ = "study_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), ForeignKey("user_study_profiles.discord_id"), nullable=False, index=True)
    
    category = Column(String(50), nullable=False, default="DSA")  # DSA, LLD, HLD, MICROSERVICES, DEVOPS_CLOUD, CORE_CS, MOCK_INTERVIEW, CUSTOM
    topic = Column(String(150), nullable=False)                   # e.g. "Kubernetes Deployments", "Dynamic Programming"
    subtopic_or_problem = Column(String(200), nullable=True)     # e.g. "Ingress & HPA", "Coin Change II"
    
    duration_minutes = Column(Integer, default=30)
    problems_solved = Column(Integer, default=1)
    confidence_score = Column(Integer, default=4)                 # 1 to 5 stars
    
    notes = Column(Text, nullable=True)
    external_link = Column(String(300), nullable=True)
    logged_at = Column(DateTime, default=get_utc_now, index=True)

    user = relationship("UserStudyProfile", back_populates="logs")

class StudyGoal(Base):
    __tablename__ = "study_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), ForeignKey("user_study_profiles.discord_id"), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    category = Column(String(50), default="DSA")
    target_count = Column(Integer, nullable=False)
    current_count = Column(Integer, default=0)
    unit = Column(String(30), default="problems")                # problems, hours, topics
    deadline = Column(String(50), nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

    user = relationship("UserStudyProfile", back_populates="goals")

class StudyStreak(Base):
    __tablename__ = "study_streaks"

    discord_id = Column(String(64), primary_key=True, index=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_study_date = Column(String(20), nullable=True)          # "YYYY-MM-DD"
    total_days_studied = Column(Integer, default=0)
    freeze_count = Column(Integer, default=2)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class PomodoroSession(Base):
    __tablename__ = "pomodoro_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), nullable=False, index=True)
    task_description = Column(String(255), nullable=False)
    category = Column(String(50), default="DSA")
    duration_minutes = Column(Integer, default=25)
    status = Column(String(30), default="COMPLETED")              # COMPLETED, ABORTED
    started_at = Column(DateTime, default=get_utc_now)
    completed_at = Column(DateTime, default=get_utc_now)

class StudyResource(Base):
    __tablename__ = "study_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)    # DSA, LLD, HLD, MICROSERVICES, DEVOPS_CLOUD, CORE_CS, CUSTOM
    topic = Column(String(150), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    resource_type = Column(String(50), default="ARTICLE")        # ARTICLE, VIDEO, DOCUMENTATION, PRACTICE, REPO, CHEATSHEET, BOOK
    description = Column(Text, nullable=True)
    added_by_discord_id = Column(String(64), nullable=True, default="OFFICIAL")
    added_by_name = Column(String(100), nullable=True, default="Curated")
    is_verified = Column(Boolean, default=True)
    upvotes = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_utc_now)

class RoadmapTopicItem(Base):
    __tablename__ = "roadmap_topic_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), ForeignKey("user_study_profiles.discord_id"), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="CUSTOM", index=True)
    topic_name = Column(String(200), nullable=False, index=True)
    subtopics = Column(Text, nullable=True)                       # JSON array of subtopics / problem names
    status = Column(String(30), default="TODO", index=True)       # TODO, IN_PROGRESS, COMPLETED
    source = Column(String(50), default="FILE_UPLOAD")            # BUILTIN, FILE_UPLOAD, MANUAL, SHARED_SCHEDULE
    order_index = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    user = relationship("UserStudyProfile", back_populates="topics")

class StudySchedulePlan(Base):
    __tablename__ = "study_schedule_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), ForeignKey("user_study_profiles.discord_id"), nullable=False, index=True)
    author_name = Column(String(100), nullable=True, default="Candidate")
    title = Column(String(200), nullable=False)
    target_exit_date = Column(String(50), nullable=True)          # e.g. "2026-11-30" or "90-Day Exit"
    daily_slots = Column(String(255), nullable=True, default="Morning: 7:30-9:00 AM, Evening: 8:30-10:00 PM")
    schedule_json = Column(Text, nullable=False)                  # JSON structure of daily slots, topics & weekly breakdown
    is_public = Column(Boolean, default=True, index=True)
    cloned_from_id = Column(Integer, nullable=True)
    clones_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    user = relationship("UserStudyProfile", back_populates="schedules")
