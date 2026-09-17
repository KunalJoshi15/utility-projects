import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base
from services.study_service import study_service, CURATED_ROADMAPS
from services.gemini_coach_service import gemini_coach_service
from services.pomodoro_service import pomodoro_service
from services.curriculum_service import curriculum_service
from services.schedule_service import schedule_service
from services.chart_service import chart_service
from services.reminder_service import reminder_service

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

def test_microservices_and_kubernetes_roadmap():
    ms_map = study_service.get_curated_roadmaps("MICROSERVICES")
    assert "MICROSERVICES" in ms_map
    topics = ms_map["MICROSERVICES"]["topics"]
    assert len(topics) >= 8

    # Verify key microservices and kubernetes domains
    topic_names = " ".join([t["name"] for t in topics])
    assert "Kubernetes" in topic_names
    assert "Helm" in topic_names
    assert "Docker" in topic_names
    assert "Distributed Transaction" in topic_names or "Saga" in topic_names
    assert "Observability" in topic_names or "OpenTelemetry" in topic_names

    # Check key problems / subtopics
    all_problems = [p for t in topics for p in t.get("key_problems", [])]
    assert any("Pod Lifecycle" in p or "HPA" in p for p in all_problems)
    assert any("Saga Pattern" in p or "Outbox" in p for p in all_problems)
    assert any("OpenTelemetry" in p or "Jaeger" in p for p in all_problems)

@pytest.mark.asyncio
async def test_resources_add_get_and_upvote(test_db: AsyncSession):
    # 1. Add user custom resource
    res = await study_service.add_resource(
        db=test_db,
        category="MICROSERVICES",
        topic="Kubernetes Ingress",
        title="Understanding K8s Ingress Controllers & NGINX Routing",
        url="https://kubernetes.io/docs/concepts/services-networking/ingress/",
        resource_type="DOCUMENTATION",
        description="Comprehensive guide to Layer 7 routing and SSL termination in Kubernetes.",
        added_by_discord_id="user_k8s_pro",
        added_by_name="K8s Dev"
    )
    assert res.id is not None
    assert res.category == "MICROSERVICES"
    assert res.upvotes == 1

    # 2. Get resources filtering by category
    results = await study_service.get_resources(test_db, category="MICROSERVICES")
    assert len(results) >= 1
    assert any(r["title"] == "Understanding K8s Ingress Controllers & NGINX Routing" for r in results)

    # 3. Search by topic keyword
    matched = await study_service.get_resources(test_db, topic="Ingress")
    assert len(matched) >= 1
    assert matched[0]["topic"] == "Kubernetes Ingress"

    # 4. Upvote resource
    updated = await study_service.upvote_resource(test_db, res.id)
    assert updated.upvotes == 2

@pytest.mark.asyncio
async def test_seed_default_resources(test_db: AsyncSession):
    await study_service.seed_default_resources(test_db)
    all_res = await study_service.get_resources(test_db)
    assert len(all_res) >= 5

    # Check that Kubernetes, Microservices, and Kafka seeded items exist
    titles = [r["title"] for r in all_res]
    assert any("Kubernetes" in t for t in titles)
    assert any("Microservices" in t or "Patterns" in t for t in titles)
    assert any("Kafka" in t or "Distributed" in t for t in titles)

@pytest.mark.asyncio
async def test_curriculum_file_and_text_parsing(test_db: AsyncSession):
    # Test Markdown/Text syllabus ingestion
    markdown_syllabus = """
# Kubernetes Core & Workloads
- [ ] Pod Lifecycle & Probes
- [ ] Deployments & Rollouts
- [ ] Ingress & Services

## Distributed Systems & Saga Pattern
- Orchestration vs Choreography
- Transactional Outbox Pattern

3. Dynamic Programming
- Coin Change II
- Longest Increasing Subsequence
"""
    items = await curriculum_service.parse_and_import_curriculum(
        db=test_db,
        discord_id="user_curriculum_1",
        content=markdown_syllabus,
        filename="syllabus.md"
    )
    assert len(items) >= 3
    
    topics = await curriculum_service.get_user_topics(test_db, "user_curriculum_1")
    assert len(topics) >= 3
    
    topic_names = [t.topic_name for t in topics]
    assert any("Kubernetes" in name for name in topic_names)
    assert any("Saga" in name or "Distributed" in name for name in topic_names)
    assert any("Dynamic Programming" in name for name in topic_names)

@pytest.mark.asyncio
async def test_topic_toggle_and_checklist(test_db: AsyncSession):
    # 1. Ingest topic
    await curriculum_service.parse_and_import_curriculum(
        db=test_db,
        discord_id="user_toggle_1",
        content="1. Kafka Partitioning & Event Sourcing\n2. SOLID Principles Machine Coding"
    )

    # 2. Check initial status (TODO)
    stats_init = await curriculum_service.get_topic_stats(test_db, "user_toggle_1")
    assert stats_init["TODO"] == 2
    assert stats_init["COMPLETED"] == 0

    # 3. Toggle to IN_PROGRESS
    t1 = await curriculum_service.toggle_topic_status(test_db, "user_toggle_1", "Kafka")
    assert t1.status == "IN_PROGRESS"

    # 4. Toggle to COMPLETED
    t2 = await curriculum_service.toggle_topic_status(test_db, "user_toggle_1", "Kafka")
    assert t2.status == "COMPLETED"
    assert t2.completed_at is not None

    stats_done = await curriculum_service.get_topic_stats(test_db, "user_toggle_1")
    assert stats_done["COMPLETED"] == 1
    assert stats_done["TODO"] == 1

@pytest.mark.asyncio
async def test_schedule_creation_adaptation_and_forking(test_db: AsyncSession):
    # 1. Create schedule with target exit date
    plan = await schedule_service.create_or_generate_schedule(
        db=test_db,
        discord_id="user_schedule_author",
        author_name="Alice Architect",
        target_exit_date="2026-11-30",
        daily_slots="Morning: 7:00-8:30 AM (DSA), Evening: 8:30-10:00 PM (K8s/LLD)",
        title="90-Day Senior Backend Exit Sprint"
    )
    assert plan.id is not None
    assert plan.target_exit_date == "2026-11-30"
    assert plan.author_name == "Alice Architect"
    assert plan.clones_count == 0

    # 2. Browse public schedules
    public_plans = await schedule_service.get_public_schedules(test_db)
    assert len(public_plans) >= 1
    assert public_plans[0].title == "90-Day Senior Backend Exit Sprint"

    # 3. Clone / fork schedule into another user's profile
    cloned = await schedule_service.clone_schedule(
        db=test_db,
        schedule_id=plan.id,
        target_discord_id="user_schedule_cloner",
        target_author_name="Bob Backend",
        custom_exit_date="2026-12-31"
    )
    assert cloned.id is not None
    assert cloned.discord_id == "user_schedule_cloner"
    assert cloned.target_exit_date == "2026-12-31"
    assert "Forked from Alice Architect" in cloned.title
    assert plan.clones_count == 1

    # 4. Adjust schedule with AI
    adjusted = await schedule_service.adjust_schedule_with_ai(
        db=test_db,
        discord_id="user_schedule_cloner",
        instruction="Allocate more weekend time for Kubernetes and Saga pattern"
    )
    assert adjusted is not None
    assert adjusted.id == cloned.id

def test_progress_chart_rendering():
    summary_data = {
        "total_hours": 12.5,
        "total_problems": 28,
        "categories": {
            "MICROSERVICES": {"total_hours": 4.5, "problems_solved": 8},
            "DSA": {"total_hours": 5.0, "problems_solved": 15},
            "LLD": {"total_hours": 3.0, "problems_solved": 5}
        }
    }
    daily_entries = [
        {"date": "2026-09-10", "minutes": 60},
        {"date": "2026-09-11", "minutes": 90},
        {"date": "2026-09-12", "minutes": 45},
        {"date": "2026-09-15", "minutes": 120}
    ]
    topic_stats = {"COMPLETED": 8, "IN_PROGRESS": 3, "TODO": 10}

    buf = chart_service.generate_progress_chart(
        display_name="Alex Dev",
        summary=summary_data,
        daily_logs=daily_entries,
        topic_stats=topic_stats
    )
    assert buf is not None
    raw_bytes = buf.getvalue()
    assert len(raw_bytes) > 1000
    # Verify PNG magic number header: \x89PNG\r\n\x1a\n
    assert raw_bytes.startswith(b"\x89PNG\r\n\x1a\n")

@pytest.mark.asyncio
async def test_reminder_service_logic(test_db: AsyncSession):
    # Create profile with reminders enabled
    prof = await study_service.get_or_create_profile(test_db, "user_remind_me", "john_coder", "John Coder")
    prof.reminders_enabled = True
    prof.reminder_hour_utc = 0
    await test_db.commit()

    # User has not studied today
    streak = await study_service.get_streak_status(test_db, "user_remind_me")
    assert streak["studied_today"] is False


@pytest.mark.asyncio
async def test_apienx_coach_json_parsing_and_model_call(monkeypatch):
    from services.gemini_coach_service import GeminiCoachService
    coach_svc = GeminiCoachService()

    sample_plan = '```json\n{"plan_title": "Google Prep", "target_company": "Google", "target_role": "SDE 2", "total_weeks": 4, "weekly_breakdown": [{"week_number": 1, "focus_area": "Trees", "dsa_targets": ["LCA"], "lld_hld_targets": ["Design Logger"], "milestone_goal": "Master trees"}], "key_success_tips": ["Stay consistent"]}\n```'
    parsed = coach_svc._clean_and_parse_json(sample_plan)
    assert parsed is not None
    assert parsed["plan_title"] == "Google Prep"
    assert len(parsed["weekly_breakdown"]) == 1

    async def mock_call(prompt):
        return sample_plan

    monkeypatch.setattr(coach_svc, "_call_ai_model", mock_call)
    plan = await coach_svc.generate_study_plan("SDE 2", "Google", weeks_available=4)
    assert plan["plan_title"] == "Google Prep"
    assert plan["target_company"] == "Google"



