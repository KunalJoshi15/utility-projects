import discord
from typing import Dict, Any, List, Optional
from database.models import StudyGoal

COLOR_PRIMARY = 0x5865F2   # Blurple
COLOR_SUCCESS = 0x57F287   # Green
COLOR_WARNING = 0xFEE75C   # Yellow
COLOR_DANGER = 0xED4245    # Red
COLOR_FIRE = 0xE67E22      # Streak Orange / Fire
COLOR_AI = 0x9B59B6        # AI Purple

def _progress_bar(percentage: float, length: int = 10) -> str:
    """Generate visual ASCII progress bar."""
    clamped = max(0.0, min(100.0, percentage))
    filled_len = int(round(length * clamped / 100))
    bar = "█" * filled_len + "░" * (length - filled_len)
    return f"`[{bar}]` **{clamped:.0f}%**"

def create_progress_embed(summary: Dict[str, Any]) -> discord.Embed:
    """Generate comprehensive visual progress report for candidate."""
    name = summary.get("display_name", "Candidate")
    streak = summary.get("streak", {})
    streak_count = streak.get("current_streak", 0)
    streak_badge = f"🔥 `{streak_count} Day Streak`" if streak_count > 0 else "⚡ `Start Your Streak Today!`"

    embed = discord.Embed(
        title=f"📊 Interview Preparation Scorecard: {name}",
        description=(
            f"**Target Role:** `{summary.get('target_role', 'Software Engineer')}` • "
            f"**Target Companies:** `{summary.get('target_companies', 'Google, Amazon')}`\n"
            f"**Current Status:** {streak_badge} • **Total Study Time:** `⏱️ {summary.get('total_hours', 0)} Hours` • **Problems Solved:** `🧩 {summary.get('total_problems', 0)}`"
        ),
        color=COLOR_PRIMARY
    )

    # 1. Weekly Momentum
    weekly_hours = summary.get("weekly_hours", 0)
    weekly_problems = summary.get("weekly_problems", 0)
    embed.add_field(
        name="⚡ 7-Day Momentum",
        value=f"• **Study Time:** `{weekly_hours} hrs`\n• **Problems Solved:** `{weekly_problems}`\n• **Sessions:** `{summary.get('total_sessions', 0)} total`",
        inline=True
    )

    # 2. Streak Stats
    embed.add_field(
        name="🔥 Streak & Consistency",
        value=f"• **Active Streak:** `{streak.get('current_streak', 0)} days`\n• **Longest Streak:** `{streak.get('longest_streak', 0)} days`\n• **Total Active Days:** `{streak.get('total_days_studied', 0)}`",
        inline=True
    )

    # 3. Categorical Breakdown
    cats = summary.get("categories", {})
    cat_lines = []
    category_emojis = {
        "DSA": "🧩",
        "LLD": "🏗️",
        "HLD": "🌐",
        "CORE_CS": "💻",
        "MOCK_INTERVIEW": "🎤",
        "CUSTOM": "🎯"
    }

    for cat_key, data in cats.items():
        emoji = category_emojis.get(cat_key, "📁")
        hours = data.get("total_hours", 0)
        probs = data.get("problems_solved", 0)
        conf = data.get("avg_confidence", 0)
        stars = "⭐" * int(round(conf)) if conf > 0 else "No rating"
        cat_lines.append(f"{emoji} **{cat_key}:** `{hours} hrs` • `{probs} problems` • Confidence: {stars}")

    embed.add_field(
        name="📚 Category Breakdown",
        value="\n".join(cat_lines),
        inline=False
    )

    # 4. Recent Topics Logged
    recent = summary.get("recent_topics", [])
    if recent:
        recent_lines = [
            f"• `{r['date']}` **[{r['category']}]** {r['subtopic']} — `{r['minutes']}m` ({'⭐'*r['confidence']})"
            for r in recent
        ]
        embed.add_field(
            name="🕒 Recent Study Activity",
            value="\n".join(recent_lines),
            inline=False
        )

    embed.set_footer(text="Log new prep with /study log • Focus timer with /study timer • AI Coach with /study coach")
    return embed

def create_streak_embed(streak_data: Dict[str, Any], display_name: str) -> discord.Embed:
    """Format daily streak card."""
    current = streak_data.get("current_streak", 0)
    longest = streak_data.get("longest_streak", 0)
    total_days = streak_data.get("total_days_studied", 0)
    studied_today = streak_data.get("studied_today", False)

    status_text = "✅ **Studied Today!** Streak is safe." if studied_today else "⚠️ **Not yet studied today!** Log a session to keep your streak alive."
    
    embed = discord.Embed(
        title=f"🔥 Preparation Streak: {display_name}",
        description=f"### Current Streak: **{current} Days** 🔥\n{status_text}",
        color=COLOR_FIRE
    )
    embed.add_field(name="🏆 Longest Streak", value=f"`{longest} Days`", inline=True)
    embed.add_field(name="📅 Total Active Days", value=f"`{total_days} Days`", inline=True)
    embed.add_field(name="🗓️ Last Studied", value=f"`{streak_data.get('last_study_date') or 'Never'}`", inline=True)

    milestone = 7 if current < 7 else 14 if current < 14 else 30 if current < 30 else 100
    progress_pct = (current / milestone) * 100.0
    embed.add_field(
        name=f"🎯 Next Milestone: {milestone}-Day Streak",
        value=_progress_bar(progress_pct),
        inline=False
    )

    embed.set_footer(text="Keep consistent! Run /study log or /study timer to log your daily progress.")
    return embed

def create_roadmap_embed(roadmap_dict: Dict[str, Any]) -> discord.Embed:
    """Format curated roadmap card."""
    first_key = list(roadmap_dict.keys())[0]
    data = roadmap_dict[first_key]

    embed = discord.Embed(
        title=data.get("title", "Interview Roadmap"),
        description=data.get("description", "Structured preparation curriculum"),
        color=COLOR_PRIMARY
    )

    topics = data.get("topics", [])
    for idx, t in enumerate(topics[:8], 1):
        problems_str = " • ".join([f"`{p}`" for p in t.get("key_problems", [])[:4]])
        embed.add_field(
            name=f"{idx}. 📌 {t.get('name')}",
            value=problems_str,
            inline=False
        )

    embed.set_footer(text="Use /study log to record your progress on any of these topics!")
    return embed

def create_study_plan_embed(plan: Dict[str, Any]) -> discord.Embed:
    """Format AI tailored weekly preparation plan."""
    embed = discord.Embed(
        title=f"🤖 AI Study Plan: {plan.get('target_role')} @ {plan.get('target_company')}",
        description=f"**Duration:** `{plan.get('total_weeks', 8)} Weeks`\n{plan.get('plan_title', '')}",
        color=COLOR_AI
    )

    for week in plan.get("weekly_breakdown", [])[:6]:
        dsa_str = ", ".join(week.get("dsa_targets", []))
        sys_str = ", ".join(week.get("lld_hld_targets", []))
        desc_text = f"• **DSA:** `{dsa_str}`\n• **LLD/HLD:** `{sys_str}`\n• 🎯 **Goal:** *{week.get('milestone_goal')}*"
        embed.add_field(
            name=f"🗓️ Week {week.get('week_number')}: {week.get('focus_area')}",
            value=desc_text,
            inline=False
        )

    tips = plan.get("key_success_tips", [])
    if tips:
        embed.add_field(
            name="💡 Principal Engineer Tips",
            value="\n".join([f"• {t}" for t in tips[:3]]),
            inline=False
        )

    embed.set_footer(text="Generated by Google Gemini AI • Track your milestones with /study goals")
    return embed

def create_quiz_embed(quiz: Dict[str, Any]) -> discord.Embed:
    """Format AI technical interview quiz question."""
    embed = discord.Embed(
        title=f"🧠 Mock Interview Quiz: {quiz.get('topic')}",
        description=f"**Category:** `{quiz.get('category')}` • **Difficulty:** `{quiz.get('difficulty')}`\n\n"
                    f"### ❓ Question:\n**{quiz.get('question')}**",
        color=COLOR_AI
    )
    hints = quiz.get("hints", [])
    if hints:
        embed.add_field(name="💡 Hint", value="\n".join([f"• {h}" for h in hints]), inline=False)

    embed.set_footer(text="Click 'Submit Answer' below to have Gemini AI evaluate your response!")
    return embed

def create_quiz_evaluation_embed(eval_data: Dict[str, Any], user_answer: str) -> discord.Embed:
    """Format AI quiz scorecard."""
    score = eval_data.get("score", 75)
    color = COLOR_SUCCESS if score >= 80 else COLOR_WARNING if score >= 60 else COLOR_DANGER

    embed = discord.Embed(
        title=f"📝 Interview Answer Evaluation (Score: {score}/100)",
        description=f"**Verdict:** **{eval_data.get('verdict', 'Evaluation Complete')}**\n\n"
                    f"**Your Answer:** *\"{user_answer[:200]}...\"*",
        color=color
    )

    strengths = eval_data.get("strengths", [])
    if strengths:
        embed.add_field(name="✅ What You Did Well", value="\n".join([f"• {s}" for s in strengths]), inline=False)

    missed = eval_data.get("missed_points", [])
    if missed:
        embed.add_field(name="⚠️ Missing Points / Blindspots", value="\n".join([f"• {m}" for m in missed]), inline=False)

    model_ans = eval_data.get("expert_model_answer")
    if model_ans:
        embed.add_field(name="💡 Ideal Staff Engineer Answer", value=model_ans, inline=False)

    takeaway = eval_data.get("actionable_takeaway")
    if takeaway:
        embed.add_field(name="🚀 Actionable Takeaway", value=f"• {takeaway}", inline=False)

    embed.set_footer(text="Evaluated with Gemini AI • Practice more with /study quiz")
    return embed

def create_revision_embed(queue: List[Dict[str, Any]]) -> discord.Embed:
    """Format Spaced Repetition revision queue."""
    embed = discord.Embed(
        title="🔄 Spaced Repetition: Topics to Revise Today",
        description="Topics you recently studied with lower confidence scores or older completion dates:",
        color=COLOR_WARNING
    )
    if not queue:
        embed.description = "🎉 **All caught up!** You have no overdue topics with low confidence."
        return embed

    for item in queue:
        stars = "⭐" * item["last_confidence"]
        embed.add_field(
            name=f"{item['urgency']} [{item['category']}] {item['subtopic']}",
            value=f"• **Confidence:** {stars} (`{item['last_confidence']}/5`)\n• **Last Studied:** `{item['days_since']} days ago`",
            inline=False
        )

    embed.set_footer(text="Run /study log after revising to update your confidence score!")
    return embed

def create_leaderboard_embed(board: List[Dict[str, Any]]) -> discord.Embed:
    """Format server study champion leaderboard."""
    embed = discord.Embed(
        title="🏆 Server Interview Preparation Leaderboard",
        description="Top preparation champions ranked by study time & problems solved:",
        color=COLOR_SUCCESS
    )

    if not board:
        embed.description = "ℹ️ No study logs found yet in this server. Start tracking with `/study log`!"
        return embed

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for idx, user in enumerate(board):
        medal = medals[idx] if idx < len(medals) else f"`#{idx+1}`"
        embed.add_field(
            name=f"{medal} {user['name']}",
            value=f"⏱️ `{user['total_hours']} hrs` • 🧩 `{user['total_problems']} solved` • 🔥 `{user['streak_days']}d streak`",
            inline=False
        )

    embed.set_footer(text="Log your daily study sessions with /study log to climb the leaderboard!")
    return embed

def create_pomodoro_embed(session_data: Dict[str, Any]) -> discord.Embed:
    """Format active Pomodoro timer embed."""
    embed = discord.Embed(
        title="⏱️ Focus Study Session (Pomodoro)",
        description=(
            f"**Task:** `{session_data['task']}`\n"
            f"**Category:** `{session_data['category']}`\n"
            f"**Duration:** `{session_data['duration_minutes']} Minutes`\n\n"
            f"🎯 Put your phone away, eliminate distractions, and focus on the task!\n"
            f"When done, click **'Complete & Log Session'** below."
        ),
        color=COLOR_PRIMARY
    )
    embed.set_footer(text="Pomodoro Focus Timer • Study Tracker Bot")
    return embed

def create_resources_embed(resources: List[Dict[str, Any]], category: Optional[str] = None) -> discord.Embed:
    """Format curated and community preparation resources embed."""
    cat_title = f" ({category.upper()})" if category else ""
    embed = discord.Embed(
        title=f"📚 Interview & Prep Learning Resources{cat_title}",
        description="Curated documentation, interactive tutorials, architecture blueprints & practice sets:",
        color=COLOR_SUCCESS
    )

    if not resources:
        embed.description = "ℹ️ No resources found for this filter. Add one with `/study resource_add`!"
        return embed

    type_emojis = {
        "DOCUMENTATION": "📖",
        "ARTICLE": "📝",
        "PRACTICE": "🧩",
        "CHEATSHEET": "⚡",
        "REPO": "🐙",
        "VIDEO": "🎥",
        "BOOK": "📕"
    }

    for idx, r in enumerate(resources[:10], 1):
        emoji = type_emojis.get(r.get("type", "").upper(), "🔗")
        field_value = (
            f"• **Type:** `{r.get('type')}` • **Added By:** `{r.get('added_by')}` • 👍 `{r.get('upvotes', 1)}`\n"
            f"• {r.get('description', '')}\n"
            f"• **[👉 Click Here to Open Resource]({r.get('url')})**"
        )
        embed.add_field(
            name=f"{idx}. {emoji} {r.get('title')} ({r.get('category')})",
            value=field_value,
            inline=False
        )

    embed.set_footer(text="Add your own favorite resources with /study resource_add or /study resource_modal")
    return embed

def create_schedule_embed(plan_obj: Any, display_name: str) -> discord.Embed:
    """Format candidate target exit schedule card."""
    import json
    data = {}
    if hasattr(plan_obj, "schedule_json") and plan_obj.schedule_json:
        try:
            data = json.loads(plan_obj.schedule_json)
        except Exception:
            data = {}

    exit_target = getattr(plan_obj, "target_exit_date", "Target Date") or "Upcoming"
    title = getattr(plan_obj, "title", "Career Exit Study Schedule")

    embed = discord.Embed(
        title=f"📅 {title}",
        description=(
            f"**Candidate:** `{display_name}` • **Target Exit Timeline:** `🎯 {exit_target}`\n"
            f"**Daily Slots:** `{getattr(plan_obj, 'daily_slots', 'Morning & Evening')}`\n"
            f"**Clones/Forks:** `👥 {getattr(plan_obj, 'clones_count', 0)}`"
        ),
        color=COLOR_PRIMARY
    )

    # Daily Time Slots
    slots = data.get("daily_time_slots", [])
    if slots:
        slot_lines = [f"• **{s.get('slot_name', 'Slot')}:** `{s.get('time')}` — *{s.get('purpose')}*" for s in slots]
        embed.add_field(name="⏰ Daily Routine Time Slots", value="\n".join(slot_lines), inline=False)

    # Weekly Milestones Breakdown
    milestones = data.get("weekly_milestones", [])
    for m in milestones[:5]:
        val = (
            f"• **Morning Slot:** {m.get('morning_focus')}\n"
            f"• **Evening Slot:** {m.get('evening_focus')}\n"
            f"• 🎯 **Milestone Deliverable:** *{m.get('weekly_deliverable')}*"
        )
        embed.add_field(
            name=f"🗓️ Week {m.get('week_num')}: {m.get('phase_title')}",
            value=val,
            inline=False
        )

    # Exit Readiness Checklist
    checklist = data.get("exit_readiness_checklist", [])
    if checklist:
        embed.add_field(
            name="🏁 Pre-Resignation Exit Readiness Checklist",
            value="\n".join([f"• [ ] {c}" for c in checklist[:4]]),
            inline=False
        )

    embed.set_footer(text="Adjust schedule anytime with /study schedule_adjust • Fork with /study schedule_clone")
    return embed

def create_shared_schedules_embed(schedules: List[Any]) -> discord.Embed:
    """Format community-shared study plans list."""
    embed = discord.Embed(
        title="🌐 Community Preparation Schedules & Roadmaps",
        description="Browse, learn from, or clone/fork fellow candidates' study routines:",
        color=COLOR_SUCCESS
    )

    if not schedules:
        embed.description = "ℹ️ No public schedules found. Generate yours with `/study schedule`!"
        return embed

    for idx, s in enumerate(schedules[:8], 1):
        field_value = (
            f"• **Author:** `{s.author_name}` • **Exit Target:** `{s.target_exit_date}` • 👥 `{s.clones_count} Forks`\n"
            f"• **Slots:** `{s.daily_slots}`\n"
            f"• 📋 **Clone into your profile:** `/study schedule_clone schedule_id:{s.id}`"
        )
        embed.add_field(
            name=f"{idx}. 📌 {s.title} (ID #{s.id})",
            value=field_value,
            inline=False
        )

    embed.set_footer(text="Clone any schedule with /study schedule_clone <id>")
    return embed

def create_topic_checklist_embed(topics: List[Any], category: Optional[str] = None, display_name: str = "Candidate") -> discord.Embed:
    """Format user checklist of roadmap topics."""
    import json
    cat_title = f" ({category.upper()})" if category else ""
    embed = discord.Embed(
        title=f"📋 Topic Checklist & Syllabus Tracker: {display_name}{cat_title}",
        description="Track and check off your preparation syllabus topics:",
        color=COLOR_PRIMARY
    )

    if not topics:
        embed.description = "ℹ️ No topics found in your checklist. Import syllabus files with `/study import_plan`!"
        return embed

    completed_count = sum(1 for t in topics if t.status == "COMPLETED")
    in_prog_count = sum(1 for t in topics if t.status == "IN_PROGRESS")
    total_count = len(topics)
    pct = (completed_count / total_count) * 100.0 if total_count > 0 else 0

    embed.description = f"**Status:** `{completed_count}/{total_count} Completed` ({pct:.0f}%) • `{in_prog_count} In Progress`"

    status_icons = {
        "COMPLETED": "✅ `[COMPLETED]`",
        "IN_PROGRESS": "🔄 `[IN PROGRESS]`",
        "TODO": "⬜ `[TODO]`"
    }

    for idx, t in enumerate(topics[:12], 1):
        icon = status_icons.get(t.status, "⬜")
        sub_list = []
        if t.subtopics:
            try:
                parsed_subs = json.loads(t.subtopics)
                if isinstance(parsed_subs, list):
                    sub_list = parsed_subs[:3]
            except Exception:
                pass
        subs_text = f" — *{', '.join(sub_list)}*" if sub_list else ""
        embed.add_field(
            name=f"{idx}. {icon} [{t.category}] {t.topic_name}",
            value=f"• Toggle status: `/study topic_toggle topic_name:\"{t.topic_name}\"`{subs_text}",
            inline=False
        )

    embed.set_footer(text="Import new topic files with /study import_plan • View graph with /study chart")
    return embed

def create_help_embed() -> discord.Embed:
    """Format Study Tracker Bot help documentation."""
    embed = discord.Embed(
        title="📚 Study Tracker & Interview Preparation Bot",
        description="Track your interview preparation, build daily streaks, practice with AI interview coaches, customize time-slotted exit schedules, and view rich graphical analytics.",
        color=COLOR_PRIMARY
    )

    embed.add_field(
        name="📝 Study Logging & Scorecards",
        value="• `/study log <category> <topic> [problems] [minutes] [confidence] [notes]` - Log study session\n"
              "• `/study quicklog` - Interactive popup modal for quick logging\n"
              "• `/study progress [user]` - View visual progress scorecard & hours\n"
              "• `/study chart [user]` - 📈 Render high-resolution graphical analytics image\n"
              "• `/study streak` - View active daily study streak & milestones\n"
              "• `/study roadmap [category]` - Browse curriculum for Microservices (K8s), DSA, LLD, HLD, Core CS",
        inline=False
    )

    embed.add_field(
        name="📁 File Curriculum Ingestion & Topic Checklists",
        value="• `/study import_plan [file] [text]` - 📥 Ingest `.md`, `.txt`, `.json`, `.yaml`, or `.csv` files into your syllabus\n"
              "• `/study topic_list [category]` - View your personal checklist of topics\n"
              "• `/study topic_toggle <topic_name> [status]` - Toggle topic status (`TODO`, `IN_PROGRESS`, `COMPLETED`)",
        inline=False
    )

    embed.add_field(
        name="🎯 Target Exit Scheduling & Social Cloning",
        value="• `/study schedule [user]` - View current time-slotted study schedule and exit countdown\n"
              "• `/study schedule_adjust <instruction>` - Prompt Gemini AI to dynamically update your schedule\n"
              "• `/study schedule_browse [query]` - Browse shared community study schedules\n"
              "• `/study schedule_clone <schedule_id>` - Clone/fork a peer's schedule into your profile\n"
              "• `/study reminders <enable> [hour_utc]` - Daily inactivity reminder notifications to protect streaks",
        inline=False
    )

    embed.add_field(
        name="📖 Learning Resources & Focus Timer",
        value="• `/study resources [category] [topic]` - Browse curated & community resources\n"
              "• `/study resource_add <category> <topic> <title> <url>` - Submit a new prep resource/link\n"
              "• `/study resource_modal` - Interactive form to share resources\n"
              "• `/study timer [duration] [task]` / `/study pomodoro` - Focus timer with auto-logging",
        inline=False
    )

    embed.add_field(
        name="🤖 Gemini AI Interview Coach",
        value="• `/study plan <role> <company> [weeks]` - Tailored preparation plan for dream companies\n"
              "• `/study quiz <topic> [difficulty]` - Mock interview technical quiz with instant grading\n"
              "• `/study revise` - Spaced repetition queue of topics needing review",
        inline=False
    )

    embed.set_footer(text="100% Free • Powered by Google Gemini AI")
    return embed
