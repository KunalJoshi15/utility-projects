import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import yaml
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, delete

from database.models import RoadmapTopicItem, UserStudyProfile
from config.settings import settings

logger = logging.getLogger(__name__)

class CurriculumService:
    """Service to parse, ingest, and track custom syllabus topics from files/text."""

    async def parse_and_import_curriculum(
        self,
        db: AsyncSession,
        discord_id: str,
        content: str,
        filename: Optional[str] = None,
        source: str = "FILE_UPLOAD"
    ) -> List[RoadmapTopicItem]:
        """Parse raw syllabus file/text into structured roadmap topics and persist to DB."""
        parsed_topics = await self._parse_content_with_ai_or_heuristic(content, filename)
        
        created_items: List[RoadmapTopicItem] = []
        for idx, t in enumerate(parsed_topics):
            topic_name = t.get("topic_name", "").strip()
            if not topic_name:
                continue

            category = t.get("category", "CUSTOM").upper()
            subtopics_list = t.get("subtopics", [])
            subtopics_json = json.dumps(subtopics_list) if isinstance(subtopics_list, list) else json.dumps([])

            # Check if topic already exists for this user
            stmt = select(RoadmapTopicItem).where(
                RoadmapTopicItem.discord_id == str(discord_id),
                RoadmapTopicItem.topic_name == topic_name
            )
            existing = (await db.execute(stmt)).scalars().first()

            if existing:
                existing.category = category
                existing.subtopics = subtopics_json
                existing.source = source
                created_items.append(existing)
            else:
                new_item = RoadmapTopicItem(
                    discord_id=str(discord_id),
                    category=category,
                    topic_name=topic_name,
                    subtopics=subtopics_json,
                    status="TODO",
                    source=source,
                    order_index=idx,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(new_item)
                created_items.append(new_item)

        await db.commit()
        return created_items

    async def _parse_content_with_ai_or_heuristic(self, content: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract structured topics using Gemini AI with robust regex/JSON fallback."""
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = f"""
You are an expert technical curriculum parser. Analyze the following study plan / syllabus text or file content and extract all preparation topics and their subtopics/problems.

Categorize each topic into one of:
- "MICROSERVICES" (Kubernetes, Docker, Helm, Saga, CQRS, Service Mesh, Kafka, Observability, OpenTelemetry)
- "DSA" (Data Structures, Algorithms, LeetCode, Dynamic Programming, Trees, Graphs)
- "LLD" (Low-Level Design, Object-Oriented Design, SOLID, Design Patterns, Machine Coding)
- "HLD" (High-Level System Design, Distributed Systems, Caching, Scaling, Rate Limiter)
- "CORE_CS" (OS, DBMS, Concurrency, Multithreading, Networks, SQL)
- "CUSTOM" (Any other topic)

Return STRICTLY valid JSON array of objects with keys:
- "topic_name": string (Clear, descriptive topic title)
- "category": string ("MICROSERVICES", "DSA", "LLD", "HLD", "CORE_CS", or "CUSTOM")
- "subtopics": array of strings (Key problems, concepts, or subtopics to cover)

File / Plan Content:
\"\"\"
{content[:6000]}
\"\"\"
"""
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
                text = response.text.strip()
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
                clean_json = match.group(1) if match else text
                parsed = json.loads(clean_json)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
            except Exception as e:
                logger.warning(f"Gemini curriculum extraction failed: {e}. Using heuristic fallback.")

        # Heuristic fallback: Parse Markdown, YAML, JSON, or Plaintext Lines
        return self._heuristic_parse(content, filename)

    def _heuristic_parse(self, content: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """Rule-based parser for markdown lists, JSON, YAML, or line outlines."""
        # 1. Try JSON
        try:
            data = json.loads(content)
            if isinstance(data, list):
                results = []
                for item in data:
                    if isinstance(item, dict):
                        results.append({
                            "topic_name": item.get("topic") or item.get("name") or item.get("title") or "Topic",
                            "category": item.get("category", "CUSTOM").upper(),
                            "subtopics": item.get("subtopics") or item.get("problems") or []
                        })
                if results:
                    return results
        except Exception:
            pass

        # 2. Try YAML
        try:
            data = yaml.safe_load(content)
            if isinstance(data, list):
                results = []
                for item in data:
                    if isinstance(item, dict):
                        results.append({
                            "topic_name": item.get("topic") or item.get("name") or item.get("title") or "Topic",
                            "category": item.get("category", "CUSTOM").upper(),
                            "subtopics": item.get("subtopics") or []
                        })
                if results:
                    return results
        except Exception:
            pass

        # 3. Line-based / Markdown parsing
        lines = content.splitlines()
        extracted: List[Dict[str, Any]] = []
        current_topic: Optional[Dict[str, Any]] = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            # Header or numbered item: '# Topic', '## Topic', '1. Topic', '- [ ] Topic'
            if line.startswith("#") or re.match(r"^\d+[\.\)]\s+", line) or line.startswith("•") or line.startswith("*"):
                name = re.sub(r"^[#\*\•\d\.\)\-\s\[\]x]+", "", line).strip()
                if not name:
                    continue

                cat = self._infer_category(name)
                current_topic = {
                    "topic_name": name,
                    "category": cat,
                    "subtopics": []
                }
                extracted.append(current_topic)
            elif line.startswith("-") or line.startswith(">"):
                sub_item = re.sub(r"^[\-\>\s\[\]x]+", "", line).strip()
                if current_topic and sub_item:
                    current_topic["subtopics"].append(sub_item)
            else:
                # Plain line
                if len(line) < 120:
                    cat = self._infer_category(line)
                    current_topic = {
                        "topic_name": line,
                        "category": cat,
                        "subtopics": []
                    }
                    extracted.append(current_topic)

        return extracted if extracted else [{"topic_name": "General Interview Prep", "category": "CUSTOM", "subtopics": []}]

    def _infer_category(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["k8s", "kubernetes", "pod", "deployment", "helm", "docker", "microservice", "saga", "cqrs", "istio", "grpc", "opentelemetry", "jaeger"]):
            return "MICROSERVICES"
        if any(w in t for w in ["tree", "graph", "dp", "dynamic programming", "array", "binary", "leetcode", "trie", "heap"]):
            return "DSA"
        if any(w in t for w in ["pattern", "lld", "solid", "parking", "tictactoe", "elevator", "factory", "singleton", "observer"]):
            return "LLD"
        if any(w in t for w in ["hld", "distributed", "caching", "sharding", "kafka", "tinyurl", "system design", "rate limit"]):
            return "HLD"
        if any(w in t for w in ["os", "dbms", "thread", "concurrency", "acid", "network", "tcp", "sql"]):
            return "CORE_CS"
        return "CUSTOM"

    async def toggle_topic_status(
        self,
        db: AsyncSession,
        discord_id: str,
        topic_name: str,
        new_status: Optional[str] = None
    ) -> Optional[RoadmapTopicItem]:
        """Toggle or set status of a topic (TODO -> IN_PROGRESS -> COMPLETED)."""
        stmt = select(RoadmapTopicItem).where(
            RoadmapTopicItem.discord_id == str(discord_id),
            RoadmapTopicItem.topic_name.ilike(f"%{topic_name}%")
        )
        item = (await db.execute(stmt)).scalars().first()
        if not item:
            return None

        if new_status:
            item.status = new_status.upper()
        else:
            # Cycle through TODO -> IN_PROGRESS -> COMPLETED -> TODO
            if item.status == "TODO":
                item.status = "IN_PROGRESS"
            elif item.status == "IN_PROGRESS":
                item.status = "COMPLETED"
                item.completed_at = datetime.now(timezone.utc)
            else:
                item.status = "TODO"
                item.completed_at = None

        if item.status == "COMPLETED" and not item.completed_at:
            item.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(item)
        return item

    async def get_user_topics(
        self,
        db: AsyncSession,
        discord_id: str,
        category: Optional[str] = None
    ) -> List[RoadmapTopicItem]:
        """Retrieve user topics with optional category filter."""
        stmt = select(RoadmapTopicItem).where(RoadmapTopicItem.discord_id == str(discord_id))
        if category:
            stmt = stmt.where(RoadmapTopicItem.category == category.upper())
        stmt = stmt.order_by(RoadmapTopicItem.order_index.asc(), RoadmapTopicItem.created_at.asc())
        return list((await db.execute(stmt)).scalars().all())

    async def get_topic_stats(self, db: AsyncSession, discord_id: str) -> Dict[str, int]:
        """Get counts of COMPLETED, IN_PROGRESS, and TODO topics."""
        topics = await self.get_user_topics(db, str(discord_id))
        stats = {"COMPLETED": 0, "IN_PROGRESS": 0, "TODO": 0}
        for t in topics:
            status = t.status.upper() if t.status else "TODO"
            stats[status] = stats.get(status, 0) + 1
        return stats

curriculum_service = CurriculumService()
