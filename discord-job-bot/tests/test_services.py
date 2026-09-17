import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base, UserProfile, CachedJob, JobApplication, JobAlert, AlertNotification, ApplyStatus, ApplyType
from services.profile_service import ProfileService
from services.job_service import JobService
from services.apply_service import ApplyService
from services.gemini_service import GeminiResumeService
from services.alert_service import AlertService

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
async def test_profile_service_crud_and_encryption(test_db: AsyncSession):
    profile_svc = ProfileService()
    
    # 1. Create Profile
    user = await profile_svc.get_or_create_profile(test_db, "123456789", "testuser")
    assert user.discord_id == "123456789"
    assert user.username == "testuser"

    # 2. Update Profile (Name & Career Details, No Personal Info)
    updated = await profile_svc.update_profile(
        db=test_db,
        discord_id="123456789",
        full_name="Alice Developer",
        years_of_experience=5,
        notice_period_days=15
    )
    assert updated.full_name == "Alice Developer"
    assert updated.username == "testuser"
    assert updated.years_of_experience == 5

    # 3. Test Cookie Encryption & Decryption
    secret_cookie = "AQEDATz0_secret_cookie_token_123"
    await profile_svc.save_linkedin_cookie(test_db, "123456789", secret_cookie)
    assert updated.linkedin_cookie_enc != secret_cookie
    decrypted = profile_svc.get_decrypted_linkedin_cookie(updated)
    assert decrypted == secret_cookie

@pytest.mark.asyncio
async def test_job_service_live_url_generation(test_db: AsyncSession):
    job_svc = JobService()

    # Search jobs
    jobs = await job_svc.search_jobs(
        db=test_db,
        query="Python Developer",
        location="Bengaluru",
        is_remote=False,
        limit=5
    )
    assert len(jobs) > 0
    first_job = jobs[0]
    assert first_job.job_id is not None
    # Verify live URLs contain direct platform domains
    assert any(domain in first_job.apply_url for domain in ["linkedin.com", "naukri.com", "google.com", "indeed.com", "remotive.com"])

@pytest.mark.asyncio
async def test_alert_service_crud(test_db: AsyncSession):
    alert_svc = AlertService()
    
    # Create Alert with all filters including timing, batch limit and delivery mode
    alert = await alert_svc.create_alert(
        db=test_db,
        discord_id="123456789",
        channel_id="9876543210",
        guild_id="111222333",
        query="Senior Backend Engineer",
        country="India",
        location="Bengaluru",
        company="Google",
        employment_type="FULLTIME",
        min_salary="₹ 35 LPA",
        delivery_mode="DM",
        frequency_hours=6,
        max_jobs_per_run=5
    )
    assert alert.id is not None
    assert alert.query == "Senior Backend Engineer"
    assert alert.country == "India"
    assert alert.location == "Bengaluru"
    assert alert.company == "Google"
    assert alert.employment_type == "FULLTIME"
    assert alert.min_salary == "₹ 35 LPA"
    assert alert.delivery_mode == "DM"
    assert alert.frequency_hours == 6
    assert alert.max_jobs_per_run == 5

    # Update Alert Schedule / Config
    updated = await alert_svc.update_alert_schedule(
        db=test_db,
        alert_id=alert.id,
        discord_id="123456789",
        frequency_hours=24,
        max_jobs_per_run=3,
        delivery_mode="CHANNEL"
    )
    assert updated.frequency_hours == 24
    assert updated.max_jobs_per_run == 3
    assert updated.delivery_mode == "CHANNEL"

    # List alerts
    alerts = await alert_svc.get_user_alerts(test_db, "123456789")
    assert len(alerts) == 1
    assert alerts[0].id == alert.id
    assert alerts[0].country == "India"
    assert alerts[0].min_salary == "₹ 35 LPA"
    assert alerts[0].delivery_mode == "CHANNEL"
    assert alerts[0].frequency_hours == 24

    # Delete alert
    deleted = await alert_svc.delete_alert(test_db, alert.id, "123456789")
    assert deleted is True
    remaining = await alert_svc.get_user_alerts(test_db, "123456789")
    assert len(remaining) == 0

@pytest.mark.asyncio
async def test_alert_digest_embed_generation(test_db: AsyncSession):
    from bot.ui.embeds import create_alert_digest_embed
    alert_svc = AlertService()
    job_svc = JobService()

    alert = await alert_svc.create_alert(
        db=test_db,
        discord_id="1122334455",
        channel_id="9988776655",
        guild_id="123",
        query="Frontend Engineer",
        country="India",
        location="Bengaluru",
        delivery_mode="DM",
        frequency_hours=12,
        max_jobs_per_run=3
    )

    jobs = await job_svc.search_jobs(test_db, query="Frontend Engineer", country="India", location="Bengaluru", limit=3)
    assert len(jobs) > 0

    embed = create_alert_digest_embed(alert, jobs)
    assert "Job Alert Digest" in embed.title
    assert "Frontend Engineer" in embed.title
    assert len(embed.fields) == len(jobs)
    assert any("Apply on" in f.value for f in embed.fields)
    assert "Private DM" in embed.description

@pytest.mark.asyncio
async def test_job_service_country_isolation_india(test_db: AsyncSession):
    job_svc = JobService()

    # Search with country="India"
    jobs = await job_svc.search_jobs(
        db=test_db,
        query="Java Developer",
        country="India",
        location="Pune",
        employment_type="INTERN",
        min_salary="₹ 12 LPA",
        limit=5
    )
    assert len(jobs) > 0
    for job in jobs:
        assert job.country == "India"
        assert "₹" in job.salary_range or "LPA" in job.salary_range or "12 LPA" in job.salary_range
        assert any(domain in job.apply_url for domain in ["in.linkedin.com", "naukri.com", "google.com", "in.indeed.com"])
        assert "f_JT=I" in job.apply_url or "naukri.com" in job.apply_url or "google.com" in job.apply_url or "indeed.com" in job.apply_url

@pytest.mark.asyncio
async def test_gemini_resume_review_heuristic():
    gemini_svc = GeminiResumeService()
    sample_resume = (
        "John Doe - Backend Software Engineer\n"
        "Experience: Responsible for writing Python and Java code. Worked on bug fixes.\n"
        "Skills: Python, SQL, Git, Docker."
    )
    review = await gemini_svc.analyze_resume(sample_resume)
    assert "ats_score" in review
    assert isinstance(review["ats_score"], int)
    assert len(review["weaknesses_and_flaws"]) > 0
    assert len(review["actionable_recommendations"]) > 0

@pytest.mark.asyncio
async def test_gemini_resume_profile_extraction():
    gemini_svc = GeminiResumeService()
    sample_resume = (
        "Jane Smith\n"
        "Senior Frontend Engineer with 4 years experience in React, TypeScript, Node.js, and AWS.\n"
    )
    profile_data = await gemini_svc.extract_resume_profile(sample_resume)
    assert "primary_role" in profile_data
    assert "skills" in profile_data
    assert len(profile_data["skills"]) > 0

def test_apply_type_detection():
    job_svc = JobService()
    assert job_svc._determine_apply_type("https://www.linkedin.com/jobs/view/123", True) == ApplyType.LINKEDIN_EASY_APPLY.value
    assert job_svc._determine_apply_type("https://www.naukri.com/job-listings-123", False) == ApplyType.DIRECT_CAREER.value
    assert job_svc._determine_apply_type("https://boards.greenhouse.io/stripe/jobs/456", False) == ApplyType.ATS_PORTAL.value
    assert job_svc._determine_apply_type("https://jobs.lever.co/airbnb/789", False) == ApplyType.ATS_PORTAL.value
    assert job_svc._determine_apply_type("https://careers.google.com/jobs/123", False) == ApplyType.DIRECT_CAREER.value

@pytest.mark.asyncio
async def test_target_companies_profile_and_search_and_alerts(test_db: AsyncSession):
    profile_svc = ProfileService()
    job_svc = JobService()
    alert_svc = AlertService()

    # 1. Save target companies in profile
    user = await profile_svc.set_target_companies(
        db=test_db,
        discord_id="999888777",
        companies="Google, Microsoft, Amazon, Swiggy",
        username="dev_user"
    )
    assert user.target_companies == "Google, Microsoft, Amazon, Swiggy"

    # 2. Search vacancies for target companies
    jobs = await job_svc.search_jobs_for_target_companies(
        db=test_db,
        user=user,
        limit=10
    )
    assert len(jobs) > 0
    assert any("Google" in j.title or "Microsoft" in j.title or "Amazon" in j.title for j in jobs)

    # 3. Create batch company alerts
    alerts = await alert_svc.create_company_alerts_for_user(
        db=test_db,
        discord_id="999888777",
        channel_id="111222333",
        role="Backend Engineer",
        min_salary="₹ 30 LPA"
    )
    assert len(alerts) == 4
    comp_names = [a.company for a in alerts]
    assert "Google" in comp_names
    assert "Microsoft" in comp_names
    assert "Amazon" in comp_names
    assert "Swiggy" in comp_names
    assert alerts[0].min_salary == "₹ 30 LPA"

@pytest.mark.asyncio
async def test_job_search_no_fake_salary_and_ambitionbox_embed(test_db: AsyncSession):
    job_svc = JobService()
    from bot.ui.embeds import create_job_embed

    # Search without min_salary
    jobs = await job_svc.search_jobs(
        db=test_db,
        query="React Developer",
        country="India",
        location="Bengaluru",
        limit=2
    )
    assert len(jobs) > 0
    first_job = jobs[0]
    # Verify salary is None / not invented
    assert first_job.salary_range is None

    # Verify embed generated contains AmbitionBox and Glassdoor benchmark links
    embed = create_job_embed(first_job, 1, len(jobs))
    field_names = [f.name for f in embed.fields]
    assert any("Market Salary Benchmarks" in name for name in field_names)
    benchmark_field = next(f for f in embed.fields if "Market Salary Benchmarks" in f.name)
    assert "ambitionbox.com" in benchmark_field.value
    assert "glassdoor.co.in" in benchmark_field.value
    assert not any("Paygrade / Salary" in name for name in field_names)

def test_salary_service_benchmarks_and_similar_roles():
    from services.salary_service import salary_service
    
    benchmarks = salary_service.get_salary_benchmarks(
        role="Senior Backend Engineer",
        company="Google",
        location="India"
    )
    
    assert benchmarks["role"] == "Senior Backend Engineer"
    assert benchmarks["company"] == "Google"
    assert "ambitionbox.com" in benchmarks["ambitionbox"]["company_role_url"]
    assert "glassdoor.co.in" in benchmarks["glassdoor"]["company_role_url"]
    assert "levels.fyi" in benchmarks["levels_fyi_url"]
    
    # Check similar roles detection
    assert len(benchmarks["similar_role_names"]) > 0
    assert len(benchmarks["ambitionbox"]["similar_roles"]) > 0
    assert len(benchmarks["glassdoor"]["similar_roles"]) > 0
    
    # Check company comparison
    comparison = salary_service.compare_salaries_across_companies(
        role="Software Engineer",
        companies=["Google", "Microsoft", "Amazon", "Swiggy"]
    )
    assert len(comparison["companies"]) == 4
    for c in comparison["companies"]:
        assert "ambitionbox.com" in c["ambitionbox_url"]
        assert "glassdoor.co.in" in c["glassdoor_url"]
        assert "levels.fyi" in c["levels_url"]

def test_visa_service_directory_and_jobs():
    from services.visa_service import visa_service
    
    # 1. Directory lookup
    germany_data = visa_service.get_country_directory("Germany")
    assert germany_data is not None
    assert "EU Blue Card" in germany_data["visa_program"]
    assert len(germany_data["top_sponsors"]) > 0
    assert any("Delivery Hero" in s["name"] or "Zalando" in s["name"] for s in germany_data["top_sponsors"])
    
    # 2. Search visa feeds
    search_data = visa_service.search_visa_jobs("Backend Developer", "Germany")
    assert search_data["country"] == "Germany"
    assert "relocate.me" in search_data["feeds"]["relocate_me"]
    assert "landing.jobs" in search_data["feeds"]["landing_jobs"]
    assert "linkedin.com" in search_data["feeds"]["linkedin_visa"]
    
    # 3. Company visa intelligence check
    intel = visa_service.check_company_visa_intel("Booking.com")
    assert intel["is_verified_in_directory"] is True
    assert len(intel["verified_sponsorship_tracks"]) > 0
    assert "Netherlands" in intel["verified_sponsorship_tracks"][0]["country"]

@pytest.mark.asyncio
async def test_job_search_visa_sponsorship_feeds(test_db: AsyncSession):
    job_svc = JobService()
    
    jobs = await job_svc.search_jobs(
        db=test_db,
        query="Full Stack Engineer",
        country="Germany",
        location="Berlin",
        visa_sponsorship=True,
        limit=5
    )
    assert len(jobs) > 0
    providers = [j.provider for j in jobs]
    assert any("Relocate.me" in p for p in providers)
    assert any("Landing.jobs" in p for p in providers)
    assert any(j.visa_sponsorship is not None for j in jobs)

@pytest.mark.asyncio
async def test_gemini_parse_job_search_prompt():
    gemini_svc = GeminiResumeService()
    prompt = "Looking for a senior backend engineer working with Python, FastAPI, Docker, and PostgreSQL in Berlin Germany with visa sponsorship"
    parsed = await gemini_svc.parse_job_search_prompt(prompt)
    
    assert "backend" in parsed["primary_role"].lower() or "senior" in parsed["seniority"].lower()
    techs = [t.lower() for t in parsed["technologies"]]
    assert any("python" in t for t in techs)
    assert any("docker" in t or "fastapi" in t for t in techs)
    assert parsed["detected_country"] == "Germany" or "berlin" in parsed["detected_location"].lower()
    assert parsed["visa_sponsorship"] is True

@pytest.mark.asyncio
async def test_gemini_evaluate_resume_fit_for_job():
    gemini_svc = GeminiResumeService()
    resume_text = (
        "Alex Dev\n"
        "Senior Software Engineer\n"
        "Skills: Python, FastAPI, AWS, Docker, PostgreSQL, Redis\n"
        "Experience: Built high-throughput microservices handling 10k RPS. Improved latency by 35%."
    )
    target_role = "Senior Python Backend Engineer"
    jd = "Seeking a Senior Backend Engineer proficient in Python, FastAPI, Kubernetes, and Kafka. Experience in microservices required."
    
    fit = await gemini_svc.evaluate_resume_fit_for_job(
        resume_text=resume_text,
        target_role=target_role,
        job_description=jd,
        company="Stripe"
    )
    
    assert "fit_score" in fit
    assert isinstance(fit["fit_score"], int)
    assert 0 <= fit["fit_score"] <= 100
    assert "verdict" in fit
    assert len(fit["matching_skills"]) > 0
    assert any("python" in s.lower() or "fastapi" in s.lower() for s in fit["matching_skills"])
    assert len(fit["missing_skills_and_gaps"]) > 0  # e.g., Kubernetes, Kafka
    assert len(fit["bullet_tailoring_tips"]) > 0

@pytest.mark.asyncio
async def test_job_service_search_by_prompt(test_db: AsyncSession):
    job_svc = JobService()
    prompt = "React and TypeScript frontend engineer jobs in Bengaluru India"
    
    parsed, jobs = await job_svc.search_jobs_by_prompt(
        db=test_db,
        prompt_text=prompt,
        user=None,
        limit=5
    )
    
    assert "react" in [t.lower() for t in parsed.get("technologies", [])]
    assert len(jobs) > 0
    for job in jobs:
        assert job.job_id is not None
        assert "India" in job.country or "Bengaluru" in job.location
        assert any(domain in job.apply_url for domain in ["linkedin.com", "naukri.com", "google.com", "indeed.com", "careers."])


@pytest.mark.asyncio
async def test_company_directory_and_target_companies_portals(test_db: AsyncSession):
    from services.company_directory import get_company_career_url, find_company_match
    
    # 1. Test Static Directory Lookups
    google_info = get_company_career_url("Google", "Backend Engineer", "Bengaluru")
    assert google_info["name"] == "Google"
    assert "careers.google.com" in google_info["home_url"] or "careers.google.com" in google_info["apply_url"] or "about/careers" in google_info["apply_url"]
    
    amazon_info = get_company_career_url("Amazon", "Software Engineer", "India")
    assert amazon_info["name"] == "Amazon"
    assert "amazon.jobs" in amazon_info["apply_url"]
    
    swiggy_info = get_company_career_url("Swiggy", "SDE 2", "Bengaluru")
    assert swiggy_info["name"] == "Swiggy"
    assert "careers.swiggy.com" in swiggy_info["apply_url"]
    
    # 2. Test search_jobs_for_target_companies
    job_svc = JobService()
    profile_svc = ProfileService()
    user = await profile_svc.get_or_create_profile(test_db, "user_comp_test", "comp_tester")
    user.target_companies = "Google, Amazon, Swiggy, Microsoft, Flipkart"
    
    jobs = await job_svc.search_jobs_for_target_companies(
        db=test_db,
        user=user,
        companies=["Google", "Amazon", "Swiggy", "Microsoft", "Flipkart"],
        limit=5
    )
    
    assert len(jobs) == 5
    assert jobs[0].company == "Google"
    assert "Google Careers" in jobs[0].provider
    assert "careers" in jobs[0].apply_url.lower() or "google" in jobs[0].apply_url.lower()
    
    assert jobs[1].company == "Amazon"
    assert "Amazon" in jobs[1].provider
    assert "amazon.jobs" in jobs[1].apply_url
    
    assert jobs[2].company == "Swiggy"
    assert "careers.swiggy.com" in jobs[2].apply_url


@pytest.mark.asyncio
async def test_gemini_discover_company_career_portal():
    from services.gemini_service import gemini_service
    
    # Test discovery for known and arbitrary companies
    portal_data = await gemini_service.discover_company_career_portal(
        company_name="Uber",
        target_role="Backend Engineer",
        location="Bengaluru"
    )
    
    assert portal_data is not None
    assert "name" in portal_data
    assert "uber" in portal_data["name"].lower()
    assert "apply_url" in portal_data
    assert "careers" in portal_data["apply_url"].lower() or "uber" in portal_data["apply_url"].lower()


@pytest.mark.asyncio
async def test_apienx_json_parsing_and_model_call(monkeypatch):
    from services.gemini_service import GeminiResumeService
    gemini_svc = GeminiResumeService()
    
    # Test JSON parser with markdown wrappers and raw json
    sample_json = '```json\n{"ats_score": 88, "summary_verdict": "Great resume", "strengths": ["Python"], "weaknesses_and_flaws": ["None"], "missing_metrics": [], "bullet_point_improvements": [], "actionable_recommendations": ["Apply now"]}\n```'
    parsed = gemini_svc._clean_and_parse_json(sample_json)
    assert parsed is not None
    assert parsed["ats_score"] == 88
    assert parsed["summary_verdict"] == "Great resume"
    
    # Test mocked _call_ai_model
    async def mock_call(prompt):
        return sample_json
    
    monkeypatch.setattr(gemini_svc, "_call_ai_model", mock_call)
    res = await gemini_svc.analyze_resume("Jane Developer with 10 years experience building scalable backend microservices and databases in Python and Go.")
    assert res["ats_score"] == 88
    assert res["strengths"] == ["Python"]





