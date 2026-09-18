from __future__ import annotations
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from database.models import Base, UserStudyProfile, DailyStudySession, StudyStreak
from services.topic_service import topic_service

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_streak_progression_and_7day_calendar(db_session: AsyncSession):
    """Test streak calculations, 7-day visual activity calendar, and milestone status."""
    discord_id = "user_streak_001"

    # 1. Initially streak details for fresh user
    details0 = await topic_service.get_user_streak_details(db=db_session, discord_id=discord_id)
    assert details0["current_streak"] == 0
    assert details0["freeze_count"] == 2
    assert details0["studied_today"] is False
    assert details0["status_tag"] == "INACTIVE"
    assert len(details0["activity_7d"]) == 7

    # 2. Log study activity today
    await topic_service.log_study_activity(
        db=db_session,
        discord_id=discord_id,
        raw_topics="1. Dynamic Programming 2. Bit Manipulation",
        notes="Bitwise tricks",
        duration_minutes=45,
        problems_solved=2,
        category="DSA",
        username="alex",
        display_name="Alex Coder"
    )

    details1 = await topic_service.get_user_streak_details(db=db_session, discord_id=discord_id)
    assert details1["current_streak"] == 1
    assert details1["longest_streak"] == 1
    assert details1["total_days_studied"] == 1
    assert details1["studied_today"] is True
    assert details1["status_tag"] == "ACTIVE_SAFE"
    assert details1["next_milestone"] == 3
    assert details1["days_to_milestone"] == 2

    # Today in activity_7d should be active
    today_entry = next(a for a in details1["activity_7d"] if a["is_today"])
    assert today_entry["is_active"] is True

@pytest.mark.asyncio
async def test_streak_freeze_consumption_and_protection(db_session: AsyncSession):
    """Test consuming a streak freeze shield protects the streak when user hasn't studied."""
    discord_id = "user_freeze_002"

    # Seed an active streak from yesterday
    yesterday_str = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
    streak_obj = StudyStreak(
        discord_id=discord_id,
        current_streak=5,
        longest_streak=5,
        last_study_date=yesterday_str,
        total_days_studied=5,
        freeze_count=2
    )
    db_session.add(streak_obj)
    await db_session.commit()

    # Status before freeze
    details_before = await topic_service.get_user_streak_details(db=db_session, discord_id=discord_id)
    assert details_before["current_streak"] == 5
    assert details_before["studied_today"] is False
    assert details_before["status_tag"] == "AT_RISK"

    # Consume 1 freeze shield
    freeze_res = await topic_service.use_streak_freeze(db=db_session, discord_id=discord_id)
    assert freeze_res["success"] is True
    assert freeze_res["remaining_freezes"] == 1
    assert freeze_res["current_streak"] == 5

    # Status after freeze
    details_after = await topic_service.get_user_streak_details(db=db_session, discord_id=discord_id)
    assert details_after["current_streak"] == 5
    assert details_after["freeze_count"] == 1
    assert details_after["studied_today"] is True
    assert details_after["status_tag"] == "ACTIVE_SAFE"

    # Trying to freeze again today should raise ValueError
    with pytest.raises(ValueError, match="already studied today"):
        await topic_service.use_streak_freeze(db=db_session, discord_id=discord_id)

@pytest.mark.asyncio
async def test_streak_milestone_shield_reward(db_session: AsyncSession):
    """Test reaching a 7-day streak rewards an additional streak freeze shield."""
    discord_id = "user_reward_003"

    # Seed a 6-day streak from yesterday
    yesterday_str = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
    streak_obj = StudyStreak(
        discord_id=discord_id,
        current_streak=6,
        longest_streak=6,
        last_study_date=yesterday_str,
        total_days_studied=6,
        freeze_count=2
    )
    db_session.add(streak_obj)
    await db_session.commit()

    # Log study today (hitting day 7 milestone)
    res = await topic_service.log_study_activity(
        db=db_session,
        discord_id=discord_id,
        raw_topics="1. Graph Algorithms: Dijkstra",
        notes="Shortest path with min-heap",
        duration_minutes=60,
        problems_solved=1,
        category="DSA",
        username="grinder",
        display_name="Grinder"
    )

    assert res["streak"] == 7

    # Check streak object has +1 freeze shield (2 + 1 = 3)
    stmt = select(StudyStreak).where(StudyStreak.discord_id == discord_id)
    updated_streak = (await db_session.execute(stmt)).scalar_one()
    assert updated_streak.current_streak == 7
    assert updated_streak.freeze_count == 3
