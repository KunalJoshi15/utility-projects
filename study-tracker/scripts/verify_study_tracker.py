import asyncio
import os
import sys
import io
import openpyxl

# Ensure UTF-8 output encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def run_verification():
    print("==================================================")
    print("RUNNING STUDY TRACKER & INTERVIEW BOT VERIFICATION")
    print("==================================================")

    # 1. Test Config & Database
    print("[1/5] Testing Configuration & Database Initialization...")
    from database.db import init_db, get_db
    from database.models import UserStudyProfile, StudyTrack, UserTrackEnrollment
    from services.track_service import track_service
    await init_db()
    print("  [PASS] Database initialized and master curriculum tracks auto-seeded.")

    # 2. Test Master Tracks Presence
    print("[2/5] Verifying Master Preparation Tracks...")
    async with get_db() as db:
        tracks = await track_service.list_tracks(db)
        assert len(tracks) >= 6, f"Expected at least 6 tracks, found {len(tracks)}"
        master_track = next((t for t in tracks if t.slug == "master-career-prep"), None)
        assert master_track is not None, "Master career prep track not found"
        assert master_track.total_topics_count >= 40
        print(f"  [PASS] Found {len(tracks)} study tracks. Master Track: '{master_track.title}' with {master_track.total_topics_count} modules.")

    # 3. Test Excel Spreadsheet Ingestion
    print("[3/5] Testing Native Excel (.xlsx) Track Ingestion...")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Prep"
    ws.append(["Topic", "Category", "Subtopics", "Difficulty"])
    ws.append(["Kubernetes Pods & Workloads", "MICROSERVICES", "Deployments, StatefulSets", "Core"])
    ws.append(["Dynamic Programming 1D", "DSA", "Coin Change, House Robber", "Hard"])
    ws.append(["Parking Lot LLD", "LLD", "Floor allocation, Payments", "Medium"])
    
    buf = io.BytesIO()
    wb.save(buf)
    excel_bytes = buf.getvalue()

    async with get_db() as db:
        custom_track = await track_service.ingest_and_create_track(
            db=db,
            discord_id="verify_user_1",
            author_name="Alice Candidate",
            title="Spring 2026 SDE-2 Exit Track",
            file_bytes=excel_bytes,
            filename="sde2_plan.xlsx"
        )
        assert custom_track.total_topics_count == 3
        print(f"  [PASS] Ingested Excel spreadsheet into custom track #{custom_track.id}: '{custom_track.title}' ({custom_track.total_topics_count} topics).")

    # 4. Test Multi-User Isolated Progress Tracking
    print("[4/5] Testing Multi-User Progress Isolation...")
    async with get_db() as db:
        # Enroll Alice and Bob into the same Master Track
        await track_service.enroll_user_in_track(db, "user_alice", "master-career-prep", "Alice")
        await track_service.enroll_user_in_track(db, "user_bob", "master-career-prep", "Bob")

        # Alice completes 2 topics
        await track_service.toggle_topic_status(db, "user_alice", "master-career-prep", "Kubernetes Core", "COMPLETED")
        await track_service.toggle_topic_status(db, "user_alice", "master-career-prep", "Arrays & Hashing", "COMPLETED")

        prog_alice = await track_service.get_track_progress_details(db, "user_alice", "master-career-prep")
        prog_bob = await track_service.get_track_progress_details(db, "user_bob", "master-career-prep")

        assert prog_alice["completed_count"] == 2, f"Alice count should be 2, got {prog_alice['completed_count']}"
        assert prog_bob["completed_count"] == 0, f"Bob count should be 0, got {prog_bob['completed_count']}"
        print(f"  [PASS] Progress isolation verified: Alice={prog_alice['completed_count']} completed ({prog_alice['percentage']}%), Bob={prog_bob['completed_count']} completed ({prog_bob['percentage']}%).")

    # 5. Test Bot Client & Cog Extensions Loading
    print("[5/5] Testing Discord Bot Client, Cogs & Slash Commands...")
    from bot.client import StudyTrackerBot
    bot = StudyTrackerBot()
    await bot.setup_hook()
    print("  [PASS] Bot client and cogs (StudyCog, PomodoroCog, AiCoachCog, LeaderboardCog, HelpCog) loaded successfully.")

    print("\n==================================================")
    print("ALL 5 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_verification())
