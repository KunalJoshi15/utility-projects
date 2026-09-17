import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, delete

from database.models import StudySchedulePlan, UserStudyProfile, RoadmapTopicItem
from services.curriculum_service import curriculum_service
from config.settings import settings

logger = logging.getLogger(__name__)

class ScheduleService:
    """Service to create, adapt, share, and clone exit-date preparation schedules."""

    async def create_or_generate_schedule(
        self,
        db: AsyncSession,
        discord_id: str,
        author_name: str,
        target_exit_date: Optional[str] = None,
        daily_slots: Optional[str] = None,
        title: Optional[str] = None,
        custom_instructions: Optional[str] = None
    ) -> StudySchedulePlan:
        """Generate a tailored time-slotted study schedule leading to target exit date."""
        # 1. Fetch user profile and roadmap topics
        prof_res = await db.execute(select(UserStudyProfile).where(UserStudyProfile.discord_id == str(discord_id)))
        profile = prof_res.scalars().first()

        exit_date = target_exit_date or (profile.target_exit_date if profile else None) or "3 Months"
        slots = daily_slots or (profile.daily_study_slots if profile else None) or "Morning: 7:30-9:00 AM, Evening: 8:30-10:00 PM"
        role = profile.target_role if profile else "Senior Software Engineer"
        companies = profile.target_companies if profile else "Google, Amazon"

        topics = await curriculum_service.get_user_topics(db, str(discord_id))
        topics_str = ", ".join([f"{t.topic_name} ({t.category})" for t in topics[:15]]) if topics else "Microservices (K8s, Saga, Kafka), DSA (Trees, DP), LLD (Design Patterns), HLD"

        schedule_data = await self._generate_schedule_json(
            role=role,
            companies=companies,
            target_exit_date=exit_date,
            daily_slots=slots,
            topics_summary=topics_str,
            custom_instructions=custom_instructions
        )

        plan_title = title or f"{role} Exit Sprint (Target: {exit_date})"
        schedule_json_str = json.dumps(schedule_data)

        # Check existing active plan
        stmt = select(StudySchedulePlan).where(StudySchedulePlan.discord_id == str(discord_id))
        existing_plan = (await db.execute(stmt)).scalars().first()

        if existing_plan:
            existing_plan.title = plan_title
            existing_plan.target_exit_date = exit_date
            existing_plan.daily_slots = slots
            existing_plan.schedule_json = schedule_json_str
            existing_plan.updated_at = datetime.now(timezone.utc)
            plan = existing_plan
        else:
            plan = StudySchedulePlan(
                discord_id=str(discord_id),
                author_name=author_name,
                title=plan_title,
                target_exit_date=exit_date,
                daily_slots=slots,
                schedule_json=schedule_json_str,
                is_public=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(plan)

        # Update profile with exit date and slots
        if profile:
            profile.target_exit_date = exit_date
            profile.daily_study_slots = slots

        await db.commit()
        await db.refresh(plan)
        return plan

    async def _generate_schedule_json(
        self,
        role: str,
        companies: str,
        target_exit_date: str,
        daily_slots: str,
        topics_summary: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call Gemini AI to construct day-by-day and time-slotted study schedule."""
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = f"""
You are an expert career transition coach and principal engineering mentor.
Create a structured, time-slotted study schedule for a candidate preparing to transition/exit their current organization.

Candidate Context:
- Target Role: {role}
- Target Dream Companies: {companies}
- Target Exit Date / Timeline: {target_exit_date}
- Daily Study Time Slots: {daily_slots}
- Key Topics / Curriculum: {topics_summary}
- Extra Preferences: {custom_instructions or "None"}

Requirements:
Return STRICTLY valid JSON with:
- "plan_title": string
- "timeline_weeks": integer (e.g. 8 or 12)
- "daily_time_slots": array of objects [{"slot_name": "Morning", "time": "7:30 - 9:00 AM", "purpose": "DSA / Concept Study"}, {"slot_name": "Evening", "time": "8:30 - 10:00 PM", "purpose": "System Design / Coding Practice"}]
- "weekly_milestones": array of 4 to 8 objects:
  - "week_num": integer
  - "phase_title": string (e.g. "Microservices & Kubernetes Foundation", "DSA Dynamic Programming Sprint")
  - "morning_focus": string
  - "evening_focus": string
  - "weekly_deliverable": string (e.g. "Implement K8s Ingress + 10 DP Problems")
- "exit_readiness_checklist": array of 4 key milestones before giving notice/resignation.
"""
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
                text = response.text.strip()
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
                clean_json = match.group(1) if match else text
                return json.loads(clean_json)
            except Exception as e:
                logger.warning(f"Gemini schedule generation failed: {e}. Using structured template.")

        # Fallback Template
        return {
            "plan_title": f"{role} Transition Schedule ({target_exit_date})",
            "timeline_weeks": 8,
            "daily_time_slots": [
                {"slot_name": "Morning Slot", "time": "7:30 AM - 9:00 AM", "purpose": "High-focus DSA & Algorithms Problem Solving"},
                {"slot_name": "Evening Slot", "time": "8:30 PM - 10:00 PM", "purpose": "Microservices (K8s/Saga) & System Design Deep Dive"}
            ],
            "weekly_milestones": [
                {"week_num": 1, "phase_title": "Kubernetes & Microservices Architecture", "morning_focus": "Arrays & Sliding Window Patterns", "evening_focus": "K8s Pods, Deployments, Services, and Helm", "weekly_deliverable": "Deploy 3-tier app on local K8s"},
                {"week_num": 2, "phase_title": "Distributed Patterns & DSA Trees/Graphs", "morning_focus": "Binary Trees & BFS/DFS Graphs", "evening_focus": "Saga Pattern (Orchestration vs Choreography) & Outbox", "weekly_deliverable": "Saga state machine implementation"},
                {"week_num": 3, "phase_title": "Event-Driven Systems & Dynamic Programming", "morning_focus": "1D & 2D Dynamic Programming (Knapsack, Coins)", "evening_focus": "Kafka Partitioning, CQRS, and Event Sourcing", "weekly_deliverable": "Kafka stream consumer with retry topics"},
                {"week_num": 4, "phase_title": "Low-Level Design & Concurrency", "morning_focus": "Thread synchronization, Mutex & Semaphores", "evening_focus": "Machine Coding (Parking Lot, Rate Limiter)", "weekly_deliverable": "Working object-oriented rate limiter"},
                {"week_num": 5, "phase_title": "High-Level Design & Observability", "morning_focus": "Heaps, Tries & Topological Sort", "evening_focus": "OpenTelemetry, Prometheus & URL Shortener HLD", "weekly_deliverable": "Full HLD architecture diagram"},
                {"week_num": 6, "phase_title": "Full Mock Interviews & Polish", "morning_focus": "Hard LeetCode problems (Company Tagged)", "evening_focus": "Mock Behavioral & System Design rounds", "weekly_deliverable": "Exit readiness review passed"}
            ],
            "exit_readiness_checklist": [
                "Solved 75+ core LeetCode pattern problems with clean O(N) complexity",
                "Built and explained Kubernetes + Kafka microservice architecture end-to-end",
                "Created production-grade LLD machine coding project (SOLID + Patterns)",
                "Resume audited and tailored to target company requirements"
            ]
        }

    async def adjust_schedule_with_ai(
        self,
        db: AsyncSession,
        discord_id: str,
        instruction: str
    ) -> Optional[StudySchedulePlan]:
        """Adapt active study schedule using Gemini AI with user instructions."""
        stmt = select(StudySchedulePlan).where(StudySchedulePlan.discord_id == str(discord_id))
        plan = (await db.execute(stmt)).scalars().first()
        if not plan:
            return None

        current_data = json.loads(plan.schedule_json) if plan.schedule_json else {}

        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = f"""
You are an expert career transition coach. Modify the following JSON study schedule according to the user's specific request.

User Modification Request:
\"{instruction}\"

Current Schedule JSON:
{json.dumps(current_data, indent=2)}

Return STRICTLY the updated JSON matching the original schema structure:
- "plan_title"
- "timeline_weeks"
- "daily_time_slots"
- "weekly_milestones"
- "exit_readiness_checklist"
"""
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
                text = response.text.strip()
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
                clean_json = match.group(1) if match else text
                updated_data = json.loads(clean_json)
                plan.schedule_json = json.dumps(updated_data)
                plan.updated_at = datetime.now(timezone.utc)
                await db.commit()
                await db.refresh(plan)
                return plan
            except Exception as e:
                logger.error(f"Error adjusting schedule with AI: {e}")

        # Fallback: append note to plan title
        plan.title = f"{plan.title} (Updated)"
        plan.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(plan)
        return plan

    async def get_user_schedule(self, db: AsyncSession, discord_id: str) -> Optional[StudySchedulePlan]:
        """Fetch active user study schedule."""
        stmt = select(StudySchedulePlan).where(StudySchedulePlan.discord_id == str(discord_id))
        return (await db.execute(stmt)).scalars().first()

    async def get_public_schedules(self, db: AsyncSession, query: Optional[str] = None, limit: int = 10) -> List[StudySchedulePlan]:
        """Browse community-shared study plans."""
        stmt = select(StudySchedulePlan).where(StudySchedulePlan.is_public == True)
        if query:
            stmt = stmt.where(StudySchedulePlan.title.ilike(f"%{query}%"))
        stmt = stmt.order_by(StudySchedulePlan.clones_count.desc(), StudySchedulePlan.updated_at.desc()).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def clone_schedule(
        self,
        db: AsyncSession,
        schedule_id: int,
        target_discord_id: str,
        target_author_name: str,
        custom_exit_date: Optional[str] = None
    ) -> Optional[StudySchedulePlan]:
        """Clone / fork a public study schedule into user's profile."""
        source_stmt = select(StudySchedulePlan).where(StudySchedulePlan.id == schedule_id)
        source_plan = (await db.execute(source_stmt)).scalars().first()
        if not source_plan:
            return None

        # Increment clone counter on source
        source_plan.clones_count += 1

        # Check existing user plan
        user_stmt = select(StudySchedulePlan).where(StudySchedulePlan.discord_id == str(target_discord_id))
        existing_user_plan = (await db.execute(user_stmt)).scalars().first()

        exit_date = custom_exit_date or source_plan.target_exit_date
        title = f"{source_plan.title} (Forked from {source_plan.author_name})"

        if existing_user_plan:
            existing_user_plan.title = title
            existing_user_plan.target_exit_date = exit_date
            existing_user_plan.daily_slots = source_plan.daily_slots
            existing_user_plan.schedule_json = source_plan.schedule_json
            existing_user_plan.cloned_from_id = source_plan.id
            existing_user_plan.updated_at = datetime.now(timezone.utc)
            cloned = existing_user_plan
        else:
            cloned = StudySchedulePlan(
                discord_id=str(target_discord_id),
                author_name=target_author_name,
                title=title,
                target_exit_date=exit_date,
                daily_slots=source_plan.daily_slots,
                schedule_json=source_plan.schedule_json,
                is_public=True,
                cloned_from_id=source_plan.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(cloned)

        await db.commit()
        await db.refresh(cloned)
        return cloned

schedule_service = ScheduleService()
