from __future__ import annotations
import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SARCASTIC_ROASTS = [
    "Your study streak is currently colder than an unheated server room in Antarctica. ❄️ Even your compiler is getting bored!",
    "404: Study effort not found today. 🔍 At this rate, ChatGPT will take your dream job before you finish LeetCode #1!",
    "The only thing you're running today is out of excuses! 🏃💨 Open your IDE before your keyboard files for abandonment.",
    "Your study graph looks like a flatline on an ECG monitor. 📈 Let's perform CPR and log at least ONE topic!",
    "Legend has it that if you don't study today, your next technical interview will be live debugging Kubernetes YAML with no internet. 💀",
    "Even an unoptimized O(n³) brute-force algorithm made more progress than you today. Drop the reels and log a topic! 🐢",
    "Your git commit graph is as blank as a fresh white sheet of paper. What happened to 'Cracking FAANG in 6 months'? 🎯",
    "The only thing you've been caching today is laziness, and the cache eviction policy has failed. 🧠 Flush the cache and start studying!",
    "Senior Engineers aren't born; they just don't ghost their study schedule like you did today. 👻",
    "Your daily study progress today: `NULL`. Not even `0`, literally `undefined`. Fix your pointer before you segfault! 💥",
    "If excuses were LeetCode submissions, you'd already be in the Top 0.1% Grandmaster tier worldwide! 🏆",
    "Breaking News: Your future employer just checked your study streak and decided to interview an AI instead. 🤖 Wake up!",
    "You've spent more time adjusting your Discord status than actually studying system design today. 🤦‍♂️",
    "Remember that dream company you wanted to join? Yeah, their interviewers are already drafting the rejection email while you slack off. ✉️",
    "Even CSS centering takes less effort than what you've done today. Let's fix that right now! 🎨",
    "Your streak is hanging by a single unhandled promise. Don't let it reject! ⚠️",
    "Did you forget your password to LeetCode, or did LeetCode forget you exist? 🚪 Log a topic and prove you're alive!",
    "You're currently on a 100% efficiency streak of doing absolutely nothing. Time for a context switch! 🔄",
    "The only stack you've been working on today is a stack of unwatched YouTube videos. 📺 Let's write some code!",
    "They say consistency beats talent. Right now, your inconsistency is winning the championship. 🥇 Get back to work!"
]

class RoastService:
    """Delivers witty, sarcastic developer jokes and roasts for inactive candidates."""

    def get_random_roast(self, username: Optional[str] = None, streak_count: int = 0) -> str:
        """Selects a punchy sarcastic roast customized with the user's name and streak context."""
        roast = random.choice(SARCASTIC_ROASTS)
        name_tag = f"**{username}**, " if username else ""

        if streak_count > 0:
            roast += f"\n\n🔥 *Your active **{streak_count}-day streak** is about to evaporate into thin air at midnight!*"
        else:
            roast += "\n\n🌱 *Your streak is currently at **0 days**. Even a 10-minute session will get you on the leaderboard!*"

        return f"{name_tag}{roast}"

    async def get_dynamic_roast(
        self,
        username: Optional[str] = None,
        streak_count: int = 0,
        recent_topics: Optional[list[str]] = None
    ) -> str:
        """Generates dynamic AI roast using Gemini / Vertex AI, falling back to curated roast list."""
        uname = username or "Candidate"
        try:
            from services.ai_service import ai_service
            ai_roast = await ai_service.generate_ai_roast(uname, streak_count=streak_count, recent_topics=recent_topics)
            if ai_roast:
                return f"**{uname}**, {ai_roast}"
        except Exception as e:
            logger.debug(f"Dynamic AI roast fallback triggered: {e}")

        return self.get_random_roast(username=username, streak_count=streak_count)

roast_service = RoastService()

