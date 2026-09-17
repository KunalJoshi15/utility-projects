from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class ApplyStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    FAILED = "FAILED"

class ApplyType(str, enum.Enum):
    LINKEDIN_EASY_APPLY = "LINKEDIN_EASY_APPLY"
    ATS_PORTAL = "ATS_PORTAL"
    DIRECT_CAREER = "DIRECT_CAREER"
    EXTERNAL_URL = "EXTERNAL_URL"

class UserProfile(Base):
    __tablename__ = "user_profiles"

    discord_id = Column(String(64), primary_key=True, index=True)
    username = Column(String(100), nullable=True)
    full_name = Column(String(150), nullable=True)
    email = Column(String(150), nullable=True)
    phone = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    
    linkedin_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    github_url = Column(String(255), nullable=True)
    
    current_role = Column(String(150), nullable=True)
    current_company = Column(String(150), nullable=True)
    years_of_experience = Column(Integer, default=0)
    notice_period_days = Column(Integer, default=30)
    requires_sponsorship = Column(Boolean, default=False)
    
    resume_file_path = Column(String(500), nullable=True)
    resume_filename = Column(String(255), nullable=True)
    
    # Encrypted session / credentials for automated applications
    linkedin_cookie_enc = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("JobAlert", back_populates="user", cascade="all, delete-orphan")


class CachedJob(Base):
    __tablename__ = "cached_jobs"

    job_id = Column(String(128), primary_key=True, index=True)
    provider = Column(String(50), default="jsearch")
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    is_remote = Column(Boolean, default=False)
    employment_type = Column(String(50), nullable=True)
    salary_range = Column(String(100), nullable=True)
    apply_type = Column(String(50), default=ApplyType.EXTERNAL_URL.value)
    apply_url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    company_logo_url = Column(String(500), nullable=True)
    posted_date = Column(String(100), nullable=True)
    cached_at = Column(DateTime, default=get_utc_now)


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), ForeignKey("user_profiles.discord_id"), nullable=False, index=True)
    job_id = Column(String(128), nullable=False)
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    apply_type = Column(String(50), default=ApplyType.EXTERNAL_URL.value)
    status = Column(String(50), default=ApplyStatus.PENDING.value)
    
    screenshot_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    applied_at = Column(DateTime, default=get_utc_now)

    user = relationship("UserProfile", back_populates="applications")


class JobAlert(Base):
    __tablename__ = "job_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(64), ForeignKey("user_profiles.discord_id"), nullable=False, index=True)
    guild_id = Column(String(64), nullable=True)
    channel_id = Column(String(64), nullable=False)
    
    query = Column(String(150), nullable=False)
    country = Column(String(100), nullable=True, default="India")
    location = Column(String(150), nullable=True)
    company = Column(String(150), nullable=True)
    employment_type = Column(String(50), nullable=True, default="FULLTIME")
    min_salary = Column(String(100), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_utc_now)

    user = relationship("UserProfile", back_populates="alerts")


class AlertNotification(Base):
    __tablename__ = "alert_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("job_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(128), nullable=False, index=True)
    notified_at = Column(DateTime, default=get_utc_now)

    __table_args__ = (
        UniqueConstraint("alert_id", "job_id", name="uq_alert_job"),
    )
