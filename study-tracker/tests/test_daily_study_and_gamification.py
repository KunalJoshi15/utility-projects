from __future__ import annotations
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database.models import Base, UserStudyProfile, DailyStudySession, StudyTopicItem, StudyStreak
from services.topic_service import topic_service
from services.gamification_service import gamification_service
from services.roast_service import roast_service

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

def test_numbered_topic_extraction():
    """Verify single, multiline, inline numbered, and bulleted topic parsing."""
    # 1. Single Topic
    res1 = topic_service.extract_numbered_topics("Dynamic Programming: 0/1 Knapsack")
    assert res1 == ["Dynamic Programming: 0/1 Knapsack"]

    # 2. Numbered Inline
    res2 = topic_service.extract_numbered_topics("1. Factory Pattern 2. Observer Pattern 3. Singleton in Java")
    assert len(res2) == 3
    assert "Factory Pattern" in res2[0]
    assert "Observer Pattern" in res2[1]
    assert "Singleton in Java" in res2[2]

    # 3. Multiline Numbered
    raw_multiline = """
    1. Rate Limiter - Token Bucket Algorithm
    2. Redis Cache Eviction & LRU Design
    3. Distributed Tracing with OpenTelemetry
    """
    res3 = topic_service.extract_numbered_topics(raw_multiline)
    assert len(res3) == 3
    assert "Rate Limiter" in res3[0]
    assert "Redis Cache" in res3[1]
    assert "Distributed Tracing" in res3[2]

    # 4. Bulleted List
    raw_bullets = """
    * Low Level Design of Splitwise
    * LeetCode #146 LRU Cache
    """
    res4 = topic_service.extract_numbered_topics(raw_bullets)
    assert len(res4) == 2
    assert "Splitwise" in res4[0]
    assert "LRU Cache" in res4[1]

@pytest.mark.asyncio
async def test_log_study_activity_single_and_multi_topic(db_session: AsyncSession):
    """Test logging single and multi-topic sessions with notes, streak and rank progression."""
    user_id = "123456789"

    # 1. Log multi-topic study with notes
    result = await topic_service.log_study_activity(
        db=db_session,
        discord_id=user_id,
        raw_topics="1. Factory Pattern 2. Observer Pattern 3. Strategy Pattern",
        notes="Understood how Strategy + Factory work together to decouple algorithms.",
        duration_minutes=60,
        problems_solved=2,
        category="LLD",
        username="Oswald",
        display_name="Oswald"
    )

    assert result["topics_count"] == 3
    assert len(result["extracted_topics"]) == 3
    assert result["duration_minutes"] == 60
    assert result["problems_solved"] == 2
    assert result["streak"] == 1
    assert result["total_topics"] == 3
    assert result["rank_info"]["title"] == "Novice Scholar"
    assert result["rank_info"]["level"] == 1

    # Verify notes retrieval
    notes_list, count = await topic_service.get_user_notes(db_session, user_id)
    assert count == 1
    assert "Strategy + Factory" in notes_list[0]["notes"]
    assert len(notes_list[0]["topics"]) == 3

    # Verify search query
    search_res, search_cnt = topic_service.extract_numbered_topics("Factory"), 1
    found_notes, found_cnt = await topic_service.get_user_notes(db_session, user_id, search_query="decouple")
    assert found_cnt == 1
    assert len(found_notes) == 1

    not_found, not_cnt = await topic_service.get_user_notes(db_session, user_id, search_query="kubernetes")
    assert not_cnt == 0
    assert len(not_found) == 0

@pytest.mark.asyncio
async def test_rank_progression_and_leaderboard(db_session: AsyncSession):
    """Test leveling up through ranks and server leaderboard sorting."""
    # User 1: 12 topics -> Code Apprentice
    topics_str = "\n".join([f"{i}. Topic {i}" for i in range(1, 13)])
    res1 = await topic_service.log_study_activity(
        db=db_session,
        discord_id="user_1",
        raw_topics=topics_str,
        duration_minutes=120,
        username="Alice",
        display_name="Alice"
    )
    assert res1["total_topics"] == 12
    assert res1["rank_info"]["title"] == "Code Apprentice"
    assert res1["rank_info"]["level"] == 2

    # User 2: 2 topics -> Novice Scholar
    await topic_service.log_study_activity(
        db=db_session,
        discord_id="user_2",
        raw_topics="1. QuickSort 2. MergeSort",
        duration_minutes=180,
        username="Bob",
        display_name="Bob"
    )

    # Check Leaderboard by Topics
    lb_topics = await gamification_service.get_leaderboard(db_session, sort_by="topics")
    assert len(lb_topics) == 2
    assert lb_topics[0]["username"] == "Alice"
    assert lb_topics[0]["total_topics"] == 12
    assert lb_topics[1]["username"] == "Bob"
    assert lb_topics[1]["total_topics"] == 2

    # Check Leaderboard by Hours
    lb_hours = await gamification_service.get_leaderboard(db_session, sort_by="hours")
    assert lb_hours[0]["username"] == "Bob" # 3.0h > 2.0h
    assert lb_hours[0]["study_hours"] == 3.0
    assert lb_hours[1]["username"] == "Alice"
    assert lb_hours[1]["study_hours"] == 2.0

def test_roast_service():
    """Verify sarcastic roast generation with custom username and streak context."""
    roast = roast_service.get_random_roast(username="Oswald", streak_count=5)
    assert "Oswald" in roast
    assert "5-day streak" in roast

@pytest.mark.asyncio
async def test_live_study_session_lifecycle(db_session: AsyncSession):
    """Verify starting, stopping, and offline auto-stopping of live study sessions."""
    from services.live_session_service import live_session_service

    user_id = "user_live_123"

    # 1. Start live session
    session = await live_session_service.start_live_session(
        db=db_session,
        discord_id=user_id,
        topic_or_goal="Kafka & Event-Driven Architecture",
        category="HLD"
    )
    assert session.discord_id == user_id
    assert session.topic_or_goal == "Kafka & Event-Driven Architecture"

    # 2. Prevent duplicate active session
    with pytest.raises(ValueError, match="already have an active study session"):
        await live_session_service.start_live_session(
            db=db_session,
            discord_id=user_id,
            topic_or_goal="Duplicate Session"
        )

    # 3. Check active session retrieval
    active = await live_session_service.get_active_session(db_session, user_id)
    assert active is not None
    assert active.topic_or_goal == "Kafka & Event-Driven Architecture"

    # 4. Stop session manually
    result = await live_session_service.stop_live_session(
        db=db_session,
        discord_id=user_id,
        notes="Learned partition rebalancing and consumer group offsets.",
        username="Oswald",
        display_name="Oswald"
    )

    assert result["topics_count"] == 1
    assert result["live_duration_minutes"] >= 1
    assert "Kafka & Event-Driven Architecture" in result["extracted_topics"][0]

    # 5. Verify active session record is deleted
    active_after = await live_session_service.get_active_session(db_session, user_id)
    assert active_after is None

    # 6. Verify logged notes
    notes_list, cnt = await topic_service.get_user_notes(db_session, user_id)
    assert cnt == 1
    assert "consumer group offsets" in notes_list[0]["notes"]

@pytest.mark.asyncio
async def test_topic_deduplication_and_problem_accumulation(db_session: AsyncSession):
    """
    Verify that studying the same topic multiple times:
    1. Updates pre-existing topic record without duplicating topic rows.
    2. Correctly accumulates problems solved and increments revision count.
    3. Keeps unique topics count accurate (total_topics_count = 1).
    4. Correctly updates total_problems_solved on user profile.
    """
    user_id = "user_dedup_1"

    # Day 1: Study Dynamic Programming and solve 3 problems
    res1 = await topic_service.log_study_activity(
        db=db_session,
        discord_id=user_id,
        raw_topics="Dynamic Programming",
        notes="Solved 0/1 Knapsack and Subset Sum",
        duration_minutes=60,
        problems_solved=3,
        category="DSA",
        username="DevUser",
        display_name="Dev User"
    )

    assert res1["total_topics"] == 1
    assert res1["total_problems"] == 3
    assert len(res1["new_topics"]) == 1
    assert len(res1["revisited_topics"]) == 0
    assert res1["new_topics"][0]["topic_name"] == "Dynamic Programming"
    assert res1["new_topics"][0]["problems_solved"] == 3

    # Day 2: Study Dynamic Programming again (case-insensitive) and solve 4 more problems
    res2 = await topic_service.log_study_activity(
        db=db_session,
        discord_id=user_id,
        raw_topics="dynamic programming",
        notes="Solved Longest Common Subsequence and Edit Distance",
        duration_minutes=45,
        problems_solved=4,
        category="DSA",
        username="DevUser",
        display_name="Dev User"
    )

    # Total unique topics should STILL be 1, but total problems should be 7
    assert res2["total_topics"] == 1
    assert res2["total_problems"] == 7
    assert len(res2["new_topics"]) == 0
    assert len(res2["revisited_topics"]) == 1
    assert res2["revisited_topics"][0]["topic_name"] == "Dynamic Programming"
    assert res2["revisited_topics"][0]["problems_added"] == 4
    assert res2["revisited_topics"][0]["total_problems"] == 7
    assert res2["revisited_topics"][0]["revision_count"] == 2

    # Verify database model values directly
    from sqlalchemy import select
    stmt = select(StudyTopicItem).where(StudyTopicItem.discord_id == user_id)
    topics = list((await db_session.execute(stmt)).scalars().all())
    assert len(topics) == 1
    assert topics[0].topic_name == "Dynamic Programming"
    assert topics[0].problems_solved == 7
    assert topics[0].revision_count == 2
    assert "Longest Common Subsequence" in topics[0].notes

    # Day 3: Study 2 topics together (1 new: Binary Trees, 1 existing: Dynamic Programming) with 5 problems
    res3 = await topic_service.log_study_activity(
        db=db_session,
        discord_id=user_id,
        raw_topics="1. Dynamic Programming 2. Binary Trees",
        notes="Mixed DP and Tree traversals",
        duration_minutes=90,
        problems_solved=5,
        category="DSA",
        username="DevUser",
        display_name="Dev User"
    )

    # 5 problems divided between 2 topics -> 3 to DP, 2 to Binary Trees
    assert res3["total_topics"] == 2
    assert res3["total_problems"] == 12 # 7 + 5
    assert len(res3["new_topics"]) == 1
    assert res3["new_topics"][0]["topic_name"] == "Binary Trees"
    assert res3["new_topics"][0]["problems_solved"] == 2
    assert len(res3["revisited_topics"]) == 1
    assert res3["revisited_topics"][0]["topic_name"] == "Dynamic Programming"
    assert res3["revisited_topics"][0]["problems_added"] == 3
    assert res3["revisited_topics"][0]["total_problems"] == 10 # 7 + 3
    assert res3["revisited_topics"][0]["revision_count"] == 3

    # Autocomplete test
    ac_all = await topic_service.get_user_existing_topics_autocomplete(db_session, user_id, "")
    assert len(ac_all) == 2
    assert "Dynamic Programming" in ac_all
    assert "Binary Trees" in ac_all

    ac_filtered = await topic_service.get_user_existing_topics_autocomplete(db_session, user_id, "dyn")
    assert ac_filtered == ["Dynamic Programming"]

