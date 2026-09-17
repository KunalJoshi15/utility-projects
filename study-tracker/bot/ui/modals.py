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
        if any(w in top_lower for w in ["k8s", "kubernetes", "pod", "helm", "docker", "microservice", "saga", "cqrs", "istio", "envoy", "grpc"]):
            category = "MICROSERVICES"
        elif any(w in top_lower for w in ["dp", "tree", "graph", "binary", "array", "leetcode", "stack", "heap", "trie"]):
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

class AddResourceModal(discord.ui.Modal, title="Add Preparation Resource"):
    title_input = discord.ui.TextInput(
        label="Resource Title (Mandatory)",
        placeholder="e.g. Kubernetes Official Documentation or Saga Pattern",
        required=True,
        max_length=150
    )
    url_input = discord.ui.TextInput(
        label="URL / Link (Mandatory)",
        placeholder="https://kubernetes.io/docs/concepts/workloads/pods/",
        required=True,
        max_length=400
    )
    category_input = discord.ui.TextInput(
        label="Category (MICROSERVICES, DSA, LLD, HLD, CORE_CS)",
        placeholder="MICROSERVICES",
        default="MICROSERVICES",
        required=True,
        max_length=30
    )
    topic_input = discord.ui.TextInput(
        label="Specific Topic / Tool",
        placeholder="e.g. Kubernetes Pods, Kafka, Redis, or Graph BFS",
        required=True,
        max_length=100
    )
    description_input = discord.ui.TextInput(
        label="Short Description / Key Takeaways",
        placeholder="Why this resource is great, key interview takeaways, or tips...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with get_db() as db:
            res = await study_service.add_resource(
                db=db,
                category=self.category_input.value.strip().upper(),
                topic=self.topic_input.value.strip(),
                title=self.title_input.value.strip(),
                url=self.url_input.value.strip(),
                description=self.description_input.value.strip() if self.description_input.value else None,
                added_by_discord_id=str(interaction.user.id),
                added_by_name=interaction.user.name,
                resource_type="ARTICLE"
            )
        await interaction.followup.send(
            f"🎉 **Resource Added Successfully!**\n"
            f"📌 **[{res.title}]({res.url})** in `{res.category}` > `{res.topic}`\n"
            f"It is now available in `/study resources` for the community to discover and upvote!",
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
        label="Category (DSA, LLD, HLD, CORE_CS, MICROSERVICES, ALL)",
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

class ScheduleAdjustModal(discord.ui.Modal, title="Adapt Study Schedule with AI"):
    instructions = discord.ui.TextInput(
        label="Instructions for Gemini AI",
        placeholder="e.g. I only have 1 hour on weekdays and 4 hours on weekends. Prioritize K8s and LLD.",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        from services.schedule_service import schedule_service
        from bot.ui.embeds import create_schedule_embed
        async with get_db() as db:
            plan = await schedule_service.adjust_schedule_with_ai(
                db=db,
                discord_id=str(interaction.user.id),
                instruction=self.instructions.value.strip()
            )

        if plan:
            embed = create_schedule_embed(plan, interaction.user.display_name or interaction.user.name)
            await interaction.followup.send(
                content="✅ **Study Schedule Adapted Successfully by Gemini AI!**",
                embed=embed,
                ephemeral=True
            )
        else:
            await interaction.followup.send("⚠️ You do not have an active schedule yet. Run `/study schedule` first!", ephemeral=True)

class PasteCurriculumModal(discord.ui.Modal, title="Paste Syllabus / Topic Outline"):
    curriculum_text = discord.ui.TextInput(
        label="Syllabus Text / Outline / Markdown",
        placeholder="Paste your syllabus lines, markdown lists, JSON, or YAML here...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=3500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        from services.curriculum_service import curriculum_service
        from bot.ui.embeds import create_topic_checklist_embed
        async with get_db() as db:
            items = await curriculum_service.parse_and_import_curriculum(
                db=db,
                discord_id=str(interaction.user.id),
                content=self.curriculum_text.value.strip(),
                source="TEXT_PASTE"
            )
            topics = await curriculum_service.get_user_topics(db, str(interaction.user.id))

        embed = create_topic_checklist_embed(topics, display_name=interaction.user.display_name or interaction.user.name)
        await interaction.followup.send(
            content=f"🎉 **Ingested {len(items)} Syllabus Topics into your Roadmap!**",
            embed=embed,
            ephemeral=True
        )
