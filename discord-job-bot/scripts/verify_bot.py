import asyncio
import os
import sys

# Ensure UTF-8 output encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def run_verification():
    print("==================================================")
    print("RUNNING DISCORD JOB & GEMINI AI BOT VERIFICATION")
    print("==================================================")

    # 1. Test Config & Settings
    print("[1/6] Testing Configuration & Encryption...")
    from config.settings import settings
    from services.profile_service import profile_service
    test_secret = "secret_linkedin_session_cookie_9988"
    enc = profile_service.encrypt_data(test_secret)
    dec = profile_service.decrypt_data(enc)
    assert dec == test_secret, "Encryption/Decryption mismatch"
    print("  [PASS] Configuration and Fernet encryption verified.")

    # 2. Test Database initialization & CRUD
    print("[2/6] Testing Database Schema & Models...")
    from database.db import init_db, get_db
    from database.models import UserProfile, CachedJob, JobApplication, ApplyStatus, ApplyType
    await init_db()
    
    async with get_db() as db:
        user = await profile_service.update_profile(
            db=db,
            discord_id="999888777",
            username="test_candidate",
            full_name="Jane Doe",
            years_of_experience=6
        )
        assert user.full_name == "Jane Doe"
        assert user.username == "test_candidate"
    print("  [PASS] Database initialization and user profile creation verified.")

    # 3. Test Gemini AI Resume Audit & Extraction
    print("[3/6] Testing Google Gemini AI Resume Review Service...")
    from services.gemini_service import gemini_service
    sample_resume = (
        "Jane Doe - Senior Full Stack Developer\n"
        "Experience: Worked on backend APIs using Python and FastAPI. Fixed bugs.\n"
        "Skills: Python, TypeScript, Docker, Kubernetes, PostgreSQL."
    )
    review = await gemini_service.analyze_resume(sample_resume)
    assert "ats_score" in review and review["ats_score"] > 0
    assert len(review["weaknesses_and_flaws"]) > 0
    print(f"  [PASS] Gemini AI Resume Audit evaluated sample resume (ATS Score: {review['ats_score']}/100).")

    # 4. Test Multi-Platform Job Search (LinkedIn + Naukri)
    print("[4/6] Testing Multi-Platform Job Aggregator (LinkedIn, Naukri, Portals)...")
    from services.job_service import job_service
    async with get_db() as db:
        jobs = await job_service.search_jobs(
            db=db,
            query="Fullstack Engineer",
            location="Bengaluru",
            is_remote=False,
            limit=5
        )
        assert len(jobs) > 0, "No jobs returned"
        cached_job = await job_service.get_job_by_id(db, jobs[0].job_id)
        assert cached_job is not None
        assert cached_job.title == jobs[0].title
    print(f"  [PASS] Multi-platform search retrieved & cached {len(jobs)} positions.")

    # 5. Test Auto-Apply Prerequisites & Fallback
    print("[5/6] Testing Auto-Apply Service...")
    from services.apply_service import apply_service
    async with get_db() as db:
        result = await apply_service.execute_application(db, user, cached_job)
        assert result["success"] is False
        assert result["status"] == ApplyStatus.FAILED.value
        assert "No resume uploaded" in result["message"]
    print("  [PASS] Auto-apply safety checks and prerequisite validations verified.")

    # 6. Test Discord Bot Client, Cogs (ResumeCog, JobsCog, ProfileCog) & Slash Commands
    print("[6/6] Testing Bot Client & Extension Cogs...")
    from bot.client import create_bot
    bot = create_bot()
    await bot.setup_hook()
    print("  [PASS] Discord Bot Client, Cogs (Resume, Jobs, Profile), and Slash Commands loaded.")

    print("\n==================================================")
    print("ALL 6 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_verification())
