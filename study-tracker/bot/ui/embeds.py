from __future__ import annotations
from typing import Dict, List, Any, Optional
import discord

# Colors
COLOR_PRIMARY = 0x5865F2   # Blurple
COLOR_SUCCESS = 0x2ECC71   # Green
COLOR_WARNING = 0xF1C40F   # Gold / Yellow
COLOR_DANGER  = 0xE74C3C   # Red
COLOR_PURPLE  = 0x9B59B6   # Purple
COLOR_AI      = 0x00D2D3   # Teal

def _progress_bar(percentage: float, length: int = 10) -> str:
    """Renders a clean ASCII/Unicode progress bar."""
    filled = int(round((percentage / 100.0) * length))
    filled = max(0, min(length, filled))
    empty = length - filled
    return f"`[{'█' * filled}{'░' * empty}]` {percentage:.0f}%"

def create_study_logged_embed(result: Dict[str, Any], display_name: str) -> discord.Embed:
    """Format celebratory embed when a study session with 1 or multiple topics is logged."""
    topics = result["extracted_topics"]
    count = result["topics_count"]
    notes = result.get("notes")
    rank_info = result.get("rank_info", {})
    did_level_up = result.get("did_level_up", False)
    new_badges = result.get("new_badges", [])
    streak = result.get("streak", 1)

    title = f"🎉 Level Up! Promoted to {rank_info.get('title')}!" if did_level_up else f"✅ Daily Study Logged ({count} Topics)"
    color = COLOR_WARNING if did_level_up else COLOR_SUCCESS

    embed = discord.Embed(
        title=title,
        description=(
            f"**Candidate:** `{display_name}` • **Rank:** {rank_info.get('icon', '🥉')} **{rank_info.get('title', 'Novice')}** (Level {rank_info.get('level', 1)})\n"
            f"**Current Streak:** 🔥 `{streak} Days Active` • **Total Topics Mastered:** `{result.get('total_topics', 0)}`\n"
            f"**Next Rank Target:** {_progress_bar(rank_info.get('progress_pct', 0))} (`{rank_info.get('topics_left', 0)} topics left`)"
        ),
        color=color
    )

    # 1. Extracted Topics Field
    topic_lines = []
    for idx, t in enumerate(topics, 1):
        topic_lines.append(f"`{idx}.` **{t}**")
    
    topics_value = "\n".join(topic_lines)
    if len(topics_value) > 1000:
        topics_value = topics_value[:980] + "\n*(more topics...)*"

    embed.add_field(
        name=f"📚 Topics Covered Today ({count} total)",
        value=topics_value,
        inline=False
    )

    # 2. Attached Notes & Takeaways
    if notes:
        notes_val = notes if len(notes) <= 1000 else notes[:980] + "..."
        embed.add_field(
            name="📝 Attached Study Notes & Takeaways",
            value=f"```markdown\n{notes_val}\n```",
            inline=False
        )

    # 3. Session Statistics
    duration_str = f"`{result.get('duration_minutes', 45)} mins`"
    probs_str = f"`{result.get('problems_solved', 0)} problems`"
    embed.add_field(
        name="⏱️ Session Details",
        value=f"• **Duration:** {duration_str}\n• **Problems Solved:** {probs_str}\n• **Category:** `{result.get('category', 'General')}`",
        inline=True
    )

    # 4. Badges Unlocked
    if new_badges:
        badge_text = "\n".join([f"• {b.icon} **{b.title}**: *{b.description}*" for b in new_badges])
        embed.add_field(
            name="🏆 New Achievements Unlocked!",
            value=badge_text[:1000],
            inline=False
        )

    embed.set_footer(text="View all your past notes with /notes • Check server leaderboard with /leaderboard")
    return embed

def create_notes_list_embed(
    notes_list: List[Dict[str, Any]],
    total_count: int,
    page: int,
    query: Optional[str],
    display_name: str
) -> discord.Embed:
    """Format paginated study notes and revision takeaways."""
    header_query = f" matching *'{query}'*" if query else ""
    embed = discord.Embed(
        title=f"📝 Study Notes & Takeaways: {display_name}{header_query}",
        description=f"Showing **{len(notes_list)}** of **{total_count}** logged note entries (Page {page + 1}):",
        color=COLOR_PRIMARY
    )

    if not notes_list:
        embed.description = f"ℹ️ No notes found{header_query}.\nLog what you study and attach notes using `/study log topics:\"...\" notes:\"...\"` or `/study quicklog`!"
        return embed

    for idx, item in enumerate(notes_list, 1):
        topics_str = ", ".join(item.get("topics", [])) or "General Session"
        notes_text = item.get("notes", "")
        if len(notes_text) > 400:
            notes_text = notes_text[:390] + "..."

        date_str = item.get("date", "Unknown Date")
        cat_str = item.get("category", "General")

        embed.add_field(
            name=f"🗓️ {date_str} [{cat_str}] — {topics_str[:180]}",
            value=f"```markdown\n{notes_text}\n```",
            inline=False
        )

    embed.set_footer(text="Search notes with /notes query:\"keyword\" • Quick log with /study quicklog")
    return embed

def create_topics_list_embed(
    topics_list: List[Any],
    total_count: int,
    display_name: str,
    rank_info: Dict[str, Any]
) -> discord.Embed:
    """Format complete topics checklist for a candidate."""
    embed = discord.Embed(
        title=f"📋 Mastered Topics Checklist: {display_name}",
        description=(
            f"**Candidate Rank:** {rank_info.get('icon', '🥉')} **{rank_info.get('title', 'Novice')}** (Level {rank_info.get('level', 1)})\n"
            f"**Total Technical Topics Covered:** `{total_count}`\n"
            f"**Rank Progress:** {_progress_bar(rank_info.get('progress_pct', 0))} (`{rank_info.get('topics_left', 0)} topics to next rank`)"
        ),
        color=COLOR_PRIMARY
    )

    if not topics_list:
        embed.description += "\n\nℹ️ You have not logged any topics yet. Run `/study log` or `/study quicklog` to start!"
        return embed

    topic_lines = []
    current_len = 0
    for idx, t in enumerate(topics_list, 1):
        line = f"`{idx}.` **{t.topic_name}** `[{t.category}]` *({t.logged_date})*"
        if current_len + len(line) + 60 > 920:
            break
        topic_lines.append(line)
        current_len += len(line) + 1

    remaining = total_count - len(topic_lines)
    if remaining > 0:
        topic_lines.append(f"*(... and `{remaining}` more topics in your history)*")

    embed.add_field(
        name=f"📚 Topics History ({len(topic_lines) if remaining <= 0 else len(topic_lines) - 1}/{total_count} shown)",
        value="\n".join(topic_lines),
        inline=False
    )

    embed.set_footer(text="Log multiple topics with numbers (e.g. 1. Topic A 2. Topic B) in /study log")
    return embed

def create_leaderboard_embed(leaderboard_data: List[Dict[str, Any]], category: str = "topics") -> discord.Embed:
    """Format high-impact server preparation leaderboard."""
    cat_titles = {
        "topics": ("📚 Top Technical Topics Mastered", "Ranked by total distinct technical topics covered:"),
        "streak": ("🔥 Longest Active Study Streaks", "Ranked by consecutive daily study streaks:"),
        "hours":  ("⏱️ Most Dedicated Study Hours", "Ranked by total study time logged:")
    }
    title, desc = cat_titles.get(category, ("🏆 Server Study Leaderboard", "Preparation champions:"))

    embed = discord.Embed(
        title=title,
        description=desc,
        color=COLOR_WARNING
    )

    if not leaderboard_data:
        embed.description = "ℹ️ No study data logged on this server yet.\nBe the first on the leaderboard with `/study log` or `/study quicklog`!"
        return embed

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for idx, user in enumerate(leaderboard_data):
        medal = medals[idx] if idx < len(medals) else f"`#{idx+1}`"
        rank_badge = f"{user.get('rank_icon', '🥉')} `{user.get('rank_title', 'Novice')}`"

        embed.add_field(
            name=f"{medal} {user['username']} — {rank_badge}",
            value=f"• **Score:** **{user['value_primary']}** ({user['value_secondary']})",
            inline=False
        )

    embed.set_footer(text="Use buttons below to switch leaderboard views • Log daily to rank up!")
    return embed

def create_profile_embed(summary: Dict[str, Any], display_name: str) -> discord.Embed:
    """Format full candidate scorecard and achievement profile."""
    prof = summary["profile"]
    rank_info = summary["rank_info"]
    streak = summary["streak"]
    badges = summary.get("badges", [])

    embed = discord.Embed(
        title=f"👤 Candidate Study Scorecard: {display_name}",
        description=(
            f"**Current Rank:** {rank_info.get('icon', '🥉')} **{rank_info.get('title')}** (Level {rank_info.get('level', 1)})\n"
            f"**Rank Progress:** {_progress_bar(rank_info.get('progress_pct', 0))} (`{rank_info.get('topics_left', 0)} topics to next rank`)\n"
            f"**Target Role:** `{prof.target_role or 'Software Engineer'}` • **Dream Companies:** `{prof.target_companies or 'FAANG'}`"
        ),
        color=COLOR_PRIMARY
    )

    # 1. Metrics Grid
    embed.add_field(
        name="📊 Preparation Metrics",
        value=(
            f"• **Topics Mastered:** `{summary.get('total_topics', 0)}`\n"
            f"• **Total Study Time:** `{summary.get('total_hours', 0)} Hours`\n"
            f"• **Problems Solved:** `{summary.get('total_problems', 0)}`"
        ),
        inline=True
    )

    # 2. Streak Metrics
    embed.add_field(
        name="🔥 Streak & Discipline",
        value=(
            f"• **Active Streak:** `{streak} Days`\n"
            f"• **Best Streak:** `{summary.get('longest_streak', 0)} Days`\n"
            f"• **Total Active Days:** `{summary.get('total_days_studied', 0)} Days`"
        ),
        inline=True
    )

    # 3. Badges Unlocked
    if badges:
        badge_text = " ".join([f"{b.icon} **{b.title}**" for b in badges[:8]])
        embed.add_field(
            name=f"🏆 Badges Earned ({len(badges)})",
            value=badge_text[:1000],
            inline=False
        )

    embed.set_footer(text="Log multiple topics with /study log • Review notes with /notes")
    return embed

def create_roast_embed(roast_text: str, slacker_name: str) -> discord.Embed:
    """Format hilarious sarcastic roast embed for Discord channels or DMs."""
    embed = discord.Embed(
        title="🔥 Daily Slacker Roast Alert! 🔥",
        description=roast_text,
        color=0xFF4757 # Sizzling crimson
    )
    embed.add_field(
        name="⚡ How to redeem yourself:",
        value=f"Run `/study log topics:\"...\"` right now, **{slacker_name}**, before the server catches on!",
        inline=False
    )
    embed.set_footer(text="Sarcasm is the highest form of motivation • Powered by Study Tracker")
    return embed

def create_live_session_started_embed(session: Any, display_name: str) -> discord.Embed:
    """Format real-time live study session start panel."""
    start_ts = int(session.start_time.timestamp()) if hasattr(session.start_time, 'timestamp') else 0
    embed = discord.Embed(
        title="🟢 Live Study Session Active",
        description=(
            f"**Candidate:** `{display_name}`\n"
            f"**Current Topic / Goal:** 🎯 **{session.topic_or_goal}**\n"
            f"**Category:** `{session.category}`\n"
            f"**Started:** <t:{start_ts}:t> (<t:{start_ts}:R>)\n\n"
            f"💡 **Session Rules:**\n"
            f"• Click **`⏹️ End Study Session`** below or run `/session stop` when finished.\n"
            f"• 🔌 **Offline Auto-Stop:** If your Discord status changes to **Offline**, your session will automatically save and conclude!"
        ),
        color=COLOR_SUCCESS
    )
    embed.set_footer(text="Stay focused! Your elapsed minutes are being tracked in real time.")
    return embed

def create_live_session_ended_embed(result: Dict[str, Any], display_name: str) -> discord.Embed:
    """Format live session completion summary receipt."""
    duration_mins = result.get("live_duration_minutes", 1)
    topics = result.get("extracted_topics", [])
    rank_info = result.get("rank_info", {})
    did_level_up = result.get("did_level_up", False)
    new_badges = result.get("new_badges", [])
    streak = result.get("streak", 1)

    title = f"🎉 Level Up! Promoted to {rank_info.get('title')}!" if did_level_up else "🏁 Live Study Session Concluded"
    color = COLOR_WARNING if did_level_up else COLOR_SUCCESS

    embed = discord.Embed(
        title=title,
        description=(
            f"**Great work, `{display_name}`!** Here is your session breakdown:\n\n"
            f"• ⏱️ **Active Duration Logged:** **`{duration_mins} Minutes`**\n"
            f"• 🔥 **Updated Streak:** **`{streak} Days Active`**\n"
            f"• 🏆 **Current Rank:** {rank_info.get('icon', '🥉')} **{rank_info.get('title', 'Novice')}** (Level {rank_info.get('level', 1)})\n"
            f"• 📚 **Total Topics Mastered:** `{result.get('total_topics', 0)}`"
        ),
        color=color
    )

    if topics:
        topic_lines = [f"`{i}.` **{t}**" for i, t in enumerate(topics, 1)]
        embed.add_field(
            name="🎯 Topics Mastered",
            value="\n".join(topic_lines)[:1000],
            inline=False
        )

    if result.get("notes"):
        embed.add_field(
            name="📝 Attached Session Notes",
            value=f"```markdown\n{result['notes'][:950]}\n```",
            inline=False
        )

    if new_badges:
        badge_text = "\n".join([f"• {b.icon} **{b.title}**: *{b.description}*" for b in new_badges])
        embed.add_field(
            name="🏆 New Badges Unlocked!",
            value=badge_text[:1000],
            inline=False
        )

    embed.set_footer(text="Start another session anytime with /session start • Check notes with /notes")
    return embed

def create_live_session_status_embed(session: Any, display_name: str) -> discord.Embed:
    """Format live session status check."""
    start_ts = int(session.start_time.timestamp()) if hasattr(session.start_time, 'timestamp') else 0
    embed = discord.Embed(
        title="⏱️ Active Study Session Status",
        description=(
            f"**Candidate:** `{display_name}`\n"
            f"**Topic / Goal:** **{session.topic_or_goal}**\n"
            f"**Category:** `{session.category}`\n"
            f"**Session Started:** <t:{start_ts}:T> (<t:{start_ts}:R>)\n"
            f"**Status:** 🟢 Live & Tracking (Auto-stops if you go offline)"
        ),
        color=COLOR_PRIMARY
    )
    embed.set_footer(text="Click 'End Study Session' when finished to save your progress!")
    return embed

def create_help_embed() -> discord.Embed:
    """Format updated Study Tracker help guide."""
    embed = discord.Embed(
        title="📚 Study Tracker Bot: Live Sessions, Topics, Notes & Leaderboards",
        description="A streamlined daily technical interview study assistant. Track live study sessions, log topics, save notes, climb leaderboards, and avoid getting roasted!",
        color=COLOR_PRIMARY
    )

    embed.add_field(
        name="⏱️ Real-Time Live Study Sessions",
        value=(
            "• `/session start [topic] [category]` - Start a live study session with real-time timer\n"
            "• `/session stop [notes] [topics]` - Conclude session and log stats\n"
            "• `/session status` - Check current elapsed time\n"
            "• 🔌 **Offline Auto-Stop:** If your Discord status goes **Offline**, the bot automatically saves your minutes!"
        ),
        inline=False
    )

    embed.add_field(
        name="📝 Daily Study & Multi-Topic Logging",
        value=(
            "• `/study log <topics> [notes] [duration] [problems] [category]`\n"
            "  *Log 1 or multiple numbered topics in a single command!*\n"
            "  *Example:* `/study log topics:\"1. Factory Pattern 2. 0/1 Knapsack DP 3. Redis Caching\" notes:\"Learned LRU eviction\"`\n"
            "• `/study quicklog` - Interactive multi-topic and notes popup modal\n"
            "• `/study profile [user]` - View candidate rank, badges, hours, and statistics\n"
            "• `/study streak` - Check your active daily study streak"
        ),
        inline=False
    )

    embed.add_field(
        name="🔍 Study Notes & Mastered Topics",
        value=(
            "• `/notes [query] [user]` - Search and browse past study notes & key takeaways\n"
            "• `/topics [user]` - View complete list of all technical topics you have mastered"
        ),
        inline=False
    )

    embed.add_field(
        name="🏆 Gamification & Server Leaderboard",
        value=(
            "• `/leaderboard [category]` - Interactive server ranking (Top Topics, Streaks, Study Hours)\n"
            "• **Ranks:** 🥉 *Novice* (1+) $\\to$ 🥈 *Apprentice* (10+) $\\to$ 🥇 *Specialist* (25+) $\\to$ 🎖️ *Artisan* (50+) $\\to$ 🔮 *Architect* (100+) $\\to$ 👑 *Champion* (250+) $\\to$ 🌟 *Grandmaster* (500+)"
        ),
        inline=False
    )

    embed.add_field(
        name="🌶️ Sarcastic Roasts",
        value=(
            "• `/roast [user]` - Drop a hilarious sarcastic roast on someone who skipped studying today\n"
            "• *Automatic Daily Check:* If you don't log any topics for the day, expect a wake-up roast!"
        ),
        inline=False
    )

    embed.set_footer(text="Consistency is key • Start today with /session start or /study quicklog")
    return embed
