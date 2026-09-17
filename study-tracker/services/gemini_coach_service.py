import os
import json
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import aiohttp
from config.settings import settings
from database.models import StudyLog

logger = logging.getLogger(__name__)

try:
    from google import genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

SAMPLE_QUIZZES = {
    "LLD": {
        "question": "In Low-Level Design, when would you choose the Strategy Pattern over the State Pattern, and how do they differ structurally?",
        "topic": "Design Patterns",
        "difficulty": "Medium",
        "ideal_points": [
            "Strategy encapsulates interchangeable algorithms chosen by client",
            "State encapsulates states of an object where state transitions alter behavior dynamically",
            "In Strategy, client typically knows which strategy to inject; in State, states transition internally"
        ]
    },
    "DSA": {
        "question": "How does the Sliding Window pattern optimize subarray problems from O(N^2) to O(N), and when does it fail on arrays with negative numbers?",
        "topic": "Sliding Window",
        "difficulty": "Medium",
        "ideal_points": [
            "Maintains a contiguous window using two pointers, expanding right and shrinking left",
            "Fails or requires prefix sums + hashmap with negative numbers because monotonic sum assumption breaks"
        ]
    },
    "HLD": {
        "question": "What is the Thundering Herd (Cache Stampede) problem in distributed caching, and how do Probabilistic Early Expiration (XFetch) or Mutex locks solve it?",
        "topic": "Caching Strategies",
        "difficulty": "Hard",
        "ideal_points": [
            "Occurs when a popular cached key expires and hundreds of concurrent requests simultaneously hit the database",
            "Mutex/Distributed lock ensures only 1 worker queries DB and warms cache while others wait",
            "XFetch proactively computes and refreshes cache before exact TTL expiration based on compute delta"
        ]
    },
    "CORE_CS": {
        "question": "What is the difference between Optimistic Concurrency Control (OCC) and Pessimistic Concurrency Control (PCC) in database transactions?",
        "topic": "DBMS & Concurrency",
        "difficulty": "Medium",
        "ideal_points": [
            "PCC locks rows upfront before reading/updating (better for high contention)",
            "OCC allows concurrent reads/writes and validates version/timestamp at commit time (better for low contention)"
        ]
    }
}

class GeminiCoachService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.apinex_api_key = getattr(settings, "APINEX_API_KEY", None) or settings.APIENX_API_KEY
        self.apinex_base_url = (getattr(settings, "APINEX_BASE_URL", None) or settings.APIENX_BASE_URL or "https://api.apinex.bond/v1").rstrip('/')
        self.ai_provider = (settings.AI_PROVIDER or "apinex").lower()
        self.model_name = settings.GEMINI_MODEL
        self.client = None
        if _GENAI_AVAILABLE and self.api_key and "AIza" in self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}")

    async def _call_ai_model(self, prompt: str) -> Optional[str]:
        """Send prompt to APInex OpenAI-compatible endpoint or Google GenAI SDK."""
        # 1. Try APInex if configured
        if (self.ai_provider in ("apinex", "apienx") or self.apinex_api_key) and self.apinex_api_key:
            url = f"{self.apinex_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.apinex_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            try:
                timeout = aiohttp.ClientTimeout(total=45)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                return data["choices"][0]["message"]["content"]
                            logger.warning(f"Unexpected response structure from APInex: {data}")
                        else:
                            error_text = await resp.text()
                            logger.warning(f"APInex request failed with status {resp.status}: {error_text}")
            except Exception as e:
                logger.error(f"Error calling APInex AI gateway: {e}")

        # 2. Fallback to Google GenAI Client if available
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                if response and hasattr(response, "text"):
                    return response.text
            except Exception as e:
                logger.error(f"Error calling Google GenAI SDK: {e}")

        return None

    def _clean_and_parse_json(self, raw_text: str) -> Optional[Any]:
        """Strip markdown fences and parse valid JSON from AI response."""
        if not raw_text:
            return None
        text = raw_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception as e:
                logger.warning(f"Regex JSON extraction failed: {e}")

        return None

    async def generate_study_plan(
        self,
        target_role: str,
        target_company: str,
        weeks_available: int = 8,
        daily_hours: float = 2.0
    ) -> Dict[str, Any]:
        """Generate tailored week-by-week interview preparation plan."""
        weeks = max(1, min(24, weeks_available))
        prompt = (
            f"You are an elite Principal Software Engineering Interview Coach. "
            f"Create a structured, week-by-week interview preparation plan for a candidate targeting "
            f"role: '{target_role}' at top tech company: '{target_company}'. "
            f"The candidate has {weeks} weeks available, studying {daily_hours} hours/day.\n"
            f"Return ONLY a clean JSON object with this exact schema:\n"
            f"{{\n"
            f'  "plan_title": "string",\n'
            f'  "target_company": "{target_company}",\n'
            f'  "target_role": "{target_role}",\n'
            f'  "total_weeks": {weeks},\n'
            f'  "weekly_breakdown": [\n'
            f'    {{\n'
            f'      "week_number": 1,\n'
            f'      "focus_area": "string (e.g. Arrays, Two Pointers & SOLID LLD)",\n'
            f'      "dsa_targets": ["string", "string"],\n'
            f'      "lld_hld_targets": ["string"],\n'
            f'      "milestone_goal": "string"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "key_success_tips": ["string", "string", "string"]\n'
            f"}}"
        )

        raw_response = await self._call_ai_model(prompt)
        if raw_response:
            parsed = self._clean_and_parse_json(raw_response)
            if isinstance(parsed, dict) and "weekly_breakdown" in parsed:
                return parsed

        # Fallback structured plan
        weekly = []
        templates = [
            ("Week 1-2: Core DSA (Arrays, Strings, Sliding Window) & SOLID Principles", ["Two Sum, 3Sum, Sliding Window Maximum", "Prefix Sums & Monotonic Stack"], ["SOLID Principles & Factory Pattern"]),
            ("Week 3-4: Trees, BST, Graphs & Behavioral Design Patterns", ["Binary Tree Traversal, LCA, Level Order", "Number of Islands, Clone Graph, Dijkstra"], ["Observer, Strategy & Decorator Patterns"]),
            ("Week 5-6: Dynamic Programming & Classic Machine Coding LLD", ["Coin Change, LIS, 0/1 Knapsack", "Word Break, Edit Distance"], ["Parking Lot LLD, Tic-Tac-Toe Game Engine"]),
            ("Week 7-8: High-Level System Design & Mock Interviews", ["Top 50 Mixed LeetCode Hard Patterns"], ["URL Shortener, WhatsApp Chat System, Rate Limiter"])
        ]
        for idx in range(weeks):
            t_idx = min(idx // 2, len(templates) - 1)
            t = templates[t_idx]
            weekly.append({
                "week_number": idx + 1,
                "focus_area": f"Phase {idx+1}: {t[0]}",
                "dsa_targets": t[1],
                "lld_hld_targets": t[2],
                "milestone_goal": f"Complete {int(daily_hours * 7 * 2)} problems / topics with >80% confidence"
            })

        return {
            "plan_title": f"{weeks}-Week Master Preparation Plan for {target_company}",
            "target_company": target_company,
            "target_role": target_role,
            "total_weeks": weeks,
            "weekly_breakdown": weekly,
            "key_success_tips": [
                "Focus on pattern recognition rather than memorizing individual solutions.",
                "Always write clean, extensible OOP code with clear class diagrams for LLD.",
                "Simulate mock interview conditions with a 25-minute timer per DSA problem."
            ]
        }

    async def generate_topic_quiz(self, topic: str, category: str = "LLD", difficulty: str = "Medium") -> Dict[str, Any]:
        """Generate an AI mock interview technical concept question."""
        prompt = (
            f"You are a Senior Staff Interviewer at a Tier-1 tech company. "
            f"Generate 1 high-yield technical concept interview question on '{topic}' under category '{category}' with difficulty '{difficulty}'.\n"
            f"Return ONLY a clean JSON object with this schema:\n"
            f"{{\n"
            f'  "question": "string",\n'
            f'  "topic": "{topic}",\n'
            f'  "category": "{category}",\n'
            f'  "difficulty": "{difficulty}",\n'
            f'  "hints": ["string", "string"],\n'
            f'  "ideal_key_points": ["string", "string", "string"]\n'
            f"}}"
        )

        raw_response = await self._call_ai_model(prompt)
        if raw_response:
            parsed = self._clean_and_parse_json(raw_response)
            if isinstance(parsed, dict) and "question" in parsed:
                return parsed

        # Fallback quiz from curated pool
        cat_key = category.upper() if category.upper() in SAMPLE_QUIZZES else "LLD"
        quiz = SAMPLE_QUIZZES[cat_key]
        return {
            "question": f"[{topic}] {quiz['question']}",
            "topic": topic,
            "category": category,
            "difficulty": difficulty,
            "hints": ["Consider real-world tradeoffs and structural class diagrams."],
            "ideal_key_points": quiz["ideal_points"]
        }

    async def evaluate_quiz_answer(self, question: str, ideal_points: List[str], user_answer: str) -> Dict[str, Any]:
        """Evaluate candidate's answer and give score & feedback."""
        prompt = (
            f"You are a Principal Engineering Interviewer. "
            f"Evaluate the candidate's answer to this technical interview question:\n"
            f"Question: {question}\n"
            f"Ideal Key Points: {ideal_points}\n"
            f"Candidate's Answer:\n\"{user_answer}\"\n\n"
            f"Return ONLY a clean JSON object with this schema:\n"
            f"{{\n"
            f'  "score": 85,  // 0 to 100\n'
            f'  "verdict": "string (Strong Answer / Good Foundation / Needs Review)",\n'
            f'  "strengths": ["string"],\n'
            f'  "missed_points": ["string"],\n'
            f'  "expert_model_answer": "string (2-3 concise sentences)",\n'
            f'  "actionable_takeaway": "string"\n'
            f"}}"
        )

        raw_response = await self._call_ai_model(prompt)
        if raw_response:
            parsed = self._clean_and_parse_json(raw_response)
            if isinstance(parsed, dict) and "score" in parsed:
                return parsed

        # Fallback heuristic evaluation
        ans_len = len(user_answer.strip())
        score = min(95, max(45, ans_len // 4 + 40))
        return {
            "score": score,
            "verdict": "Strong Answer" if score >= 80 else "Good Foundation",
            "strengths": ["Clear conceptual understanding demonstrated in answer."],
            "missed_points": ideal_points[:2],
            "expert_model_answer": " ".join(ideal_points),
            "actionable_takeaway": "Practice explaining trade-offs concisely in under 60 seconds."
        }

    def get_spaced_repetition_queue(self, logs: List[StudyLog]) -> List[Dict[str, Any]]:
        """Identify topics needing revision based on low confidence scores and time elapsed."""
        now = datetime.now(timezone.utc)
        queue = []
        for l in logs:
            log_time = l.logged_at.replace(tzinfo=timezone.utc) if l.logged_at.tzinfo is None else l.logged_at
            days_ago = (now - log_time).days
            
            # Need revision if confidence <= 3 or studied > 7 days ago
            needs_revision = (l.confidence_score <= 3) or (days_ago >= 7 and l.confidence_score < 5)
            if needs_revision:
                queue.append({
                    "topic": l.topic,
                    "subtopic": l.subtopic_or_problem or l.topic,
                    "category": l.category,
                    "last_confidence": l.confidence_score,
                    "days_since": days_ago,
                    "urgency": "High 🔥" if l.confidence_score <= 2 else "Medium ⏳"
                })

        # Sort by urgency / low confidence first
        queue.sort(key=lambda x: x["last_confidence"])
        return queue[:8]

gemini_coach_service = GeminiCoachService()
