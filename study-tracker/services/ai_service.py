from __future__ import annotations
import os
import json
import logging
from typing import Dict, Any, List, Optional
import aiohttp
from config.settings import settings

logger = logging.getLogger(__name__)

class StudyTrackerAIService:
    """
    Modular AI Service for Study Tracker, supporting Google Gemini, Vertex AI, and OpenRouter.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None
    ):
        self.gemini_api_key = gemini_api_key or getattr(settings, "GEMINI_API_KEY", None) or getattr(settings, "VERTEX_API_KEY", None)
        self.gemini_model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        self.gcp_project = getattr(settings, "GCP_PROJECT_ID", "seraphic-rune-366616")
        self.gcp_location = getattr(settings, "GCP_LOCATION", "us-central1")
        self.ai_provider = getattr(settings, "AI_PROVIDER", "auto")

        self.api_key = api_key or getattr(settings, "OPENROUTER_API_KEY", None)
        self.base_url = (base_url or getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")).rstrip('/')
        self.default_model = default_model or getattr(settings, "OPENROUTER_MODEL", "inclusionai/ling-3.0-flash-vl:free")
        self.site_url = getattr(settings, "OPENROUTER_SITE_URL", "https://discord-job-bot.local")
        self.app_name = getattr(settings, "OPENROUTER_APP_NAME", "Study Tracker Coach Bot")

    async def call_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.4
    ) -> Optional[str]:
        """Calls Google Gemini API or Google Cloud Vertex AI directly."""
        key = self.gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("VERTEX_API_KEY") or os.getenv("GOOGLE_API_KEY")
        model_name = model or self.gemini_model or "gemini-2.5-flash"
        clean_model = model_name.replace("models/", "")

        # 1. Try google.genai SDK
        try:
            from google import genai
            from google.genai import types
            client = None
            if key and not key.startswith("your_"):
                if key.startswith("AQ.") or self.ai_provider == "vertex":
                    client = genai.Client(vertexai=True, api_key=key, project=self.gcp_project, location=self.gcp_location)
                else:
                    client = genai.Client(api_key=key)
            elif self.gcp_project:
                client = genai.Client(vertexai=True, project=self.gcp_project, location=self.gcp_location)

            if client:
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_prompt if system_prompt else None
                )
                response = await client.aio.models.generate_content(
                    model=clean_model,
                    contents=prompt,
                    config=config
                )
                if response and response.text:
                    return response.text
        except Exception as e:
            logger.debug(f"google.genai SDK call in StudyTracker failed: {e}")

        # 2. Try direct Google AI Studio REST API
        if key and not key.startswith("your_"):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={key}"
                payload: Dict[str, Any] = {
                    "contents": [{
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": temperature
                    }
                }
                if system_prompt:
                    payload["systemInstruction"] = {
                        "parts": [{"text": system_prompt}]
                    }
                timeout = aiohttp.ClientTimeout(total=8)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    return parts[0].get("text", "")
            except Exception as e:
                logger.warning(f"Direct Gemini REST API in StudyTracker failed: {e}")

        return None

    async def call_chat_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: Optional[int] = None,
        timeout_seconds: int = 6
    ) -> Optional[str]:
        """Executes AI completion with automatic Gemini/Vertex AI and OpenRouter fallback."""
        key = self.gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("VERTEX_API_KEY") or os.getenv("GOOGLE_API_KEY")
        has_credentials = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or (key and not key.startswith("your_")))
        if (self.ai_provider in ("gemini", "vertex", "auto") and has_credentials) or self.ai_provider in ("gemini", "vertex"):
            gemini_res = await self.call_gemini(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            if gemini_res:
                return gemini_res


        # OpenRouter fallback
        if self.api_key and not self.api_key.startswith("your_"):
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url,
                "X-Title": self.app_name
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload: Dict[str, Any] = {
                "model": model or self.default_model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens

            try:
                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                if "message" in choice and "content" in choice["message"]:
                                    return choice["message"]["content"]
            except Exception as e:
                logger.debug(f"OpenRouter query failed in StudyTracker: {e}")

        # Try Gemini if key wasn't checked before
        if not (key and not key.startswith("your_")):
            gemini_res = await self.call_gemini(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            if gemini_res:
                return gemini_res

        return None

    async def generate_ai_roast(
        self,
        username: str,
        streak_count: int = 0,
        recent_topics: Optional[List[str]] = None
    ) -> Optional[str]:
        """Generates a dynamic, hilarious sarcastic developer roast for inactive study candidates."""
        topics_str = f"They previously studied: {', '.join(recent_topics)}." if recent_topics else "They haven't logged any topics yet."
        system_prompt = (
            "You are a witty, hilarious, sarcastic Tech Lead and AI Study Coach. "
            "Write a short, punchy, 2-3 sentence roast calling out a candidate for slacking off, not studying today, "
            "or risking their study streak. Keep it funny, full of tech humor (LeetCode, Git, AWS, System Design, ChatGPT taking jobs), "
            "and end with a motivating push to log at least one topic right now. Use emojis."
        )
        prompt = f"Target Candidate: {username}\nCurrent Streak: {streak_count} days\n{topics_str}"

        try:
            res = await self.call_chat_completion(prompt, system_prompt=system_prompt, temperature=0.7)
            if res:
                return res.strip()
        except Exception as e:
            logger.debug(f"AI roast generation failed: {e}")

        return None

ai_service = StudyTrackerAIService()
