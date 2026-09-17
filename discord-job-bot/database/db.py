import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config.settings import settings
from database.models import Base

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

# Create session maker
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db() -> None:
    """Initialize database tables and run lightweight migrations."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
            # Auto-migrate columns if table already exists in SQLite
            try:
                # Check job_alerts columns
                alert_cols = await conn.execute(
                    text("PRAGMA table_info(job_alerts)")
                )
                existing_alert_cols = [row[1] for row in alert_cols.fetchall()]
                
                if existing_alert_cols:
                    if "country" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN country VARCHAR(100) DEFAULT 'India'"))
                    if "company" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN company VARCHAR(150)"))
                    if "employment_type" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN employment_type VARCHAR(50) DEFAULT 'FULLTIME'"))
                    if "min_salary" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN min_salary VARCHAR(100)"))
                    if "visa_sponsorship" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN visa_sponsorship BOOLEAN DEFAULT 0"))
                    if "delivery_mode" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN delivery_mode VARCHAR(20) DEFAULT 'DM'"))
                    if "frequency_hours" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN frequency_hours INTEGER DEFAULT 12"))
                    if "max_jobs_per_run" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN max_jobs_per_run INTEGER DEFAULT 3"))
                    if "last_triggered_at" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN last_triggered_at DATETIME"))
                    if "preferred_hour_utc" not in existing_alert_cols:
                        await conn.execute(text("ALTER TABLE job_alerts ADD COLUMN preferred_hour_utc INTEGER"))
                
                # Check cached_jobs columns
                job_cols = await conn.execute(
                    text("PRAGMA table_info(cached_jobs)")
                )
                existing_job_cols = [row[1] for row in job_cols.fetchall()]
                if existing_job_cols:
                    if "country" not in existing_job_cols:
                        await conn.execute(text("ALTER TABLE cached_jobs ADD COLUMN country VARCHAR(100)"))
                    if "visa_sponsorship" not in existing_job_cols:
                        await conn.execute(text("ALTER TABLE cached_jobs ADD COLUMN visa_sponsorship VARCHAR(100)"))

                # Check user_profiles columns
                profile_cols = await conn.execute(
                    text("PRAGMA table_info(user_profiles)")
                )
                existing_profile_cols = [row[1] for row in profile_cols.fetchall()]
                if existing_profile_cols and "target_companies" not in existing_profile_cols:
                    await conn.execute(text("ALTER TABLE user_profiles ADD COLUMN target_companies TEXT"))

            except Exception as mig_err:
                logger.debug(f"Migration note (skipped or already applied): {mig_err}")

        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
