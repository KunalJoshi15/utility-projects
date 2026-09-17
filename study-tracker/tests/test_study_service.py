import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base
from services.study_service import study_service, CURATED_ROADMAPS
from services.gemini_coach_service import gemini_coach_service
from services.pomodoro_service import pomodoro_service

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_profile_creation_and_update(test_db: AsyncSession):
    # 1. Initialize Profile with only name and auto-populated Discord ID
    profile = await study_service.get_or_create_profile(test_db, "user_12345", "alex_dev", "Alex Developer")
    assert profile.discord_id == "user_12345"
    assert profile.display_name == "Alex Developer"

    # 2. Update preparation targets
    updated = await study_service.update_profile(
        db=test_db,
        discord_id="user_12345",
        target_role="Senior Backend Engineer",
        target_companies="Google, Microsoft, Amazon",
        daily_goal_minutes=150
    )
    assert updated.target_role == "Senior Backend Engineer"
    assert updated.target_companies == "Google, Microsoft, Amazon"
    assert updated.daily_goal_minutes == 150

@pytest.mark.asyncio
async def test_study_logging_and_streak(test_db: AsyncSession):
    # 1. Log DSA session
    log1 = await study_service.log_session(
        db=test_db,
        discord_id="user_12345",
        category="DSA",
        topic="Dynamic Programming",
        subtopic_or_problem="Coin Change II",
        duration_minutes=45,
        problems_solved=2,
        confidence_score=5,
        notes="Solved with 1D DP tabulation O(N*Amount)"
    )
    assert log1.id is not None
    assert log1.category == "DSA"
    assert log1.duration_minutes == 45
    assert log1.problems_solved == 2
    assert log1.confidence_score == 5

    # 2. Check streak
    streak = await study_service.get_streak_status(test_db, "user_12345")
    assert streak["current_streak"] == 1
    assert streak["total_days_studied"] == 1
    assert streak["studied_today"] is True

@pytest.mark.asyncio
async def test_goals_and_auto_increment(test_db: AsyncSession):
    # 1. Create a goal
    goal = await study_service.create_goal(
        db=test_db,
        discord_id="user_12345",
        title="Solve 10 LLD Problems",
        target_count=10,
        category="LLD",
        unit="problems"
    )
    assert goal.id is not None
    assert goal.current_count == 0
    assert goal.is_completed is False

    # 2. Log LLD session (should auto-increment goal)
    await study_service.log_session(
        db=test_db,
        discord_id="user_12345",
        category="LLD",
        topic="Observer Pattern",
        subtopic_or_problem="Weather Station / Pub-Sub",
        duration_minutes=30,
        problems_solved=2
    )

    goals = await study_service.get_goals(test_db, "user_12345")
    assert len(goals) == 1
    assert goals[0].current_count == 2
    assert goals[0].is_completed is False

@pytest.mark.asyncio
async def test_progress_summary_and_category_breakdown(test_db: AsyncSession):
    # Log multi-category prep
    await study_service.log_session(test_db, "user_999", "DSA", "Graphs", "Number of Islands", duration_minutes=60, problems_solved=3, confidence_score=4)
    await study_service.log_session(test_db, "user_999", "LLD", "SOLID", "Open Closed Principle", duration_minutes=30, problems_solved=1, confidence_score=5)
    await study_service.log_session(test_db, "user_999", "HLD", "Caching", "Cache Aside Redis", duration_minutes=60, problems_solved=1, confidence_score=4)

    summary = await study_service.get_user_progress_summary(test_db, "user_999")
    assert summary["total_hours"] == 2.5
    assert summary["total_problems"] == 5
    assert summary["total_sessions"] == 3
    assert summary["categories"]["DSA"]["problems_solved"] == 3
    assert summary["categories"]["LLD"]["problems_solved"] == 1
    assert summary["categories"]["HLD"]["total_hours"] == 1.0

def test_curated_roadmaps():
    dsa_map = study_service.get_curated_roadmaps("DSA")
    assert "DSA" in dsa_map
    assert len(dsa_map["DSA"]["topics"]) >= 5
    assert any("Dynamic Programming" in t["name"] for t in dsa_map["DSA"]["topics"])

    lld_map = study_service.get_curated_roadmaps("LLD")
    assert "LLD" in lld_map
    assert any("Parking Lot" in t["name"] for t in lld_map["LLD"]["topics"])

@pytest.mark.asyncio
async def test_gemini_coach_study_plan():
    plan = await gemini_coach_service.generate_study_plan(
        target_role="Senior Backend Engineer",
        target_company="Google",
        weeks_available=6
    )
    assert plan["total_weeks"] == 6
    assert len(plan["weekly_breakdown"]) == 6
    assert len(plan["key_success_tips"]) > 0

@pytest.mark.asyncio
async def test_gemini_coach_quiz_and_evaluation():
    quiz = await gemini_coach_service.generate_topic_quiz(
        topic="Strategy vs State Pattern",
        category="LLD",
        difficulty="Medium"
    )
    assert "question" in quiz
    assert len(quiz["ideal_key_points"]) > 0

    evaluation = await gemini_coach_service.evaluate_quiz_answer(
        question=quiz["question"],
        ideal_points=quiz["ideal_key_points"],
        user_answer="Strategy is for interchangeable algorithms chosen by client, while State changes behavior based on internal object state transitions."
    )
    assert "score" in evaluation
    assert isinstance(evaluation["score"], int)
    assert 0 <= evaluation["score"] <= 100
    assert "verdict" in evaluation

@pytest.mark.asyncio
async def test_pomodoro_session_lifecycle(test_db: AsyncSession):
    # 1. Start Session
    sess = pomodoro_service.start_session("pomo_user", "Solve Hard Graph Problem", category="DSA", duration_minutes=25)
    assert sess["status"] == "RUNNING"
    assert pomodoro_service.get_active_session("pomo_user") is not None

    # 2. Complete Session
    completed = await pomodoro_service.complete_session(test_db, "pomo_user")
    assert completed["task"] == "Solve Hard Graph Problem"
    assert pomodoro_service.get_active_session("pomo_user") is None

    # Verify auto-logged in study progress
    summary = await study_service.get_user_progress_summary(test_db, "pomo_user")
    assert summary["total_sessions"] == 1
    assert summary["total_hours"] == 0.4  # 25 minutes = ~0.4 hrs

@pytest.mark.asyncio
async def test_leaderboard_calculation(test_db: AsyncSession):
    await study_service.log_session(test_db, "u1", "DSA", "Trees", duration_minutes=120, problems_solved=4, username="Alice")
    await study_service.log_session(test_db, "u2", "LLD", "Patterns", duration_minutes=60, problems_solved=2, username="Bob")

    board = await study_service.get_leaderboard(test_db, limit=5)
    assert len(board) == 2
    assert board[0]["name"] == "Alice"
    assert board[0]["total_hours"] == 2.0
    assert board[1]["name"] == "Bob"
    assert board[1]["total_hours"] == 1.0
