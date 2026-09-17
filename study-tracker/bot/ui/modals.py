import discord
from database.db import get_db
from services.study_service import study_service
from services.gemini_coach_service import gemini_coach_service
from bot.ui.embeds import create_progress_embed, create_quiz_evaluation_embed

class QuickStudyLogModal(discord.ui.Modal, title="Log Study Session"):
    topic = discord.ui.TextInput(
        label="Topic / Subject (Mandatory)",
        placeholder="e.g. Dynamic Programming or Observer Pattern",
        required=True,
        max_length=100
    )
    problem_title = discord.ui.TextInput(
        label="Problem / Project Title",
        placeholder="e.g. Coin Change II or Parking Lot LLD",
        required=False,
        max_length=150
    )
    duration_minutes = discord.ui.TextInput(
        label="Duration (Minutes)",
        placeholder="e.g. 45",
        default="30",
        required=True,
        max_length=4
    )
    problems_solved = discord.ui.TextInput(
        label="Problems Solved Count",
        placeholder="e.g. 2",
        default="1",
        required=False,
        max_length=3
    )
    confidence = discord.ui.TextInput(
        label="Confidence Rating (1 to 5 Stars)",
        placeholder="e.g. 4",
        default="4",
        required=False,
        max_length=1
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            dur = int(self.duration_minutes.value.strip())
        except ValueError:
            dur = 30

        try:
            probs = int(self.problems_solved.value.strip())
        except ValueError:
            probs = 1

        try:
            conf = int(self.confidence.value.strip())
        except ValueError:
            conf = 4

        # Infer category from topic keywords
        top_lower = f"{self.topic.value} {self.problem_title.value}".lower()
        if any(w in top_lower for w in ["dp", "tree", "graph", "binary", "array", "leetcode", "stack", "heap", "trie"]):
            category = "DSA"
        elif any(w in top_lower for w in ["pattern", "lld", "solid", "parking", "tictactoe", "elevator", "factory", "singleton", "observer"]):
            category = "LLD"
        elif any(w in top_lower for w in ["hld", "distributed", "caching", "sharding", "kafka", "tinyurl", "system design"]):
            category = "HLD"
        elif any(w in top_lower for w in ["os", "dbms", "threads", "concurrency", "network", "sql", "acid"]):
            category = "CORE_CS"
        else:
            category = "CUSTOM"

        async with get_db() as db:
            log = await study_service.log_session(
                db=db,
                discord_id=str(interaction.user.id),
                category=category,
                topic=self.topic.value.strip(),
                subtopic_or_problem=self.problem_title.value.strip() if self.problem_title.value else None,
                duration_minutes=dur,
                problems_solved=probs,
                confidence_score=conf,
                username=interaction.user.name
            )
            summary = await study_service.get_user_progress_summary(db, str(interaction.user.id))

        embed = create_progress_embed(summary)
        await interaction.followup.send(
            content=f"✅ **Study Session Logged!** (`{dur}m` on **{log.topic}**). Keep up the momentum!",
            embed=embed,
            ephemeral=True
        )

class CreateGoalModal(discord.ui.Modal, title="Create Preparation Goal"):
    goal_title = discord.ui.TextInput(
        label="Goal Description",
        placeholder="e.g. Solve 50 Dynamic Programming Problems",
        required=True,
        max_length=150
    )
    target_count = discord.ui.TextInput(
        label="Target Count (Problems or Hours)",
        placeholder="e.g. 50",
        required=True,
        max_length=4
    )
    category = discord.ui.TextInput(
        label="Category (DSA, LLD, HLD, CORE_CS, ALL)",
        placeholder="e.g. DSA",
        default="DSA",
        required=True,
        max_length=20
    )
    deadline = discord.ui.TextInput(
        label="Target Deadline (Optional)",
        placeholder="e.g. Dec 31, 2026 or 4 Weeks",
        required=False,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target = int(self.target_count.value.strip())
        except ValueError:
            target = 10

        async with get_db() as db:
            goal = await study_service.create_goal(
                db=db,
                discord_id=str(interaction.user.id),
                title=self.goal_title.value.strip(),
                target_count=target,
                category=self.category.value.strip(),
                deadline=self.deadline.value.strip() if self.deadline.value else None
            )

        await interaction.followup.send(
            f"🎯 **Goal Created!** `{goal.title}` (Target: `{goal.target_count} {goal.unit}`)\n"
            f"View all goals anytime with `/study goals`.",
            ephemeral=True
        )

class QuizAnswerModal(discord.ui.Modal, title="Submit Interview Answer"):
    def __init__(self, question: str, ideal_points: list):
        super().__init__()
        self.question = question
        self.ideal_points = ideal_points
        self.answer = discord.ui.TextInput(
            label="Your Answer / Explanation",
            placeholder="Type your explanation, trade-offs, and key design decisions here...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2500
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        eval_data = await gemini_coach_service.evaluate_quiz_answer(
            question=self.question,
            ideal_points=self.ideal_points,
            user_answer=self.answer.value.strip()
        )
        embed = create_quiz_evaluation_embed(eval_data, self.answer.value.strip())
        await interaction.followup.send(embed=embed, ephemeral=True)
