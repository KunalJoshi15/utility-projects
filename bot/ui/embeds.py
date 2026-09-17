import discord
import urllib.parse
from typing import List, Dict, Any
from database.models import CachedJob, UserProfile, JobApplication, ApplyType, ApplyStatus

# Color palette for modern Discord bot theme
COLOR_PRIMARY = 0x5865F2     # Blurple
COLOR_SUCCESS = 0x57F287     # Green
COLOR_WARNING = 0xFEE75C     # Yellow
COLOR_DANGER = 0xED4245      # Red
COLOR_INFO = 0xEB459E        # Fuchsia
COLOR_GEMINI = 0x1A73E8      # Google AI Blue

def create_job_embed(job: CachedJob, current_idx: int = 1, total_count: int = 1) -> discord.Embed:
    """Format clean, accurate single job card embed focused on profile, location, real salary/AmbitionBox, and direct apply link."""
    provider_name = job.provider.replace("_", " ").title()
    
    embed = discord.Embed(
        title=f"💼 {job.title}",
        url=job.apply_url,
        color=COLOR_PRIMARY
    )
    
    embed.add_field(name="📍 Location", value=f"`{job.location}` {'(Remote 🏠)' if job.is_remote else ''}", inline=True)
    embed.add_field(name="🕒 Employment Type", value=f"`{job.employment_type}`", inline=True)
    
    # Only display salary if explicitly disclosed / filtered
    if job.salary_range and job.salary_range.lower() not in ("competitive", "not disclosed", "none", "competitive salary"):
        embed.add_field(name="💰 Disclosed Salary", value=f"`{job.salary_range}`", inline=True)

    if job.company and "Live" not in job.company and "Portal" not in job.company:
        embed.add_field(name="🏢 Company", value=f"`{job.company}`", inline=True)

    # AmbitionBox salary estimation link
    clean_title = job.title.split("—")[-1].strip() if "—" in job.title else job.title
    comp_query = job.company if (job.company and "Live" not in job.company and "Portal" not in job.company) else ""
    
    if comp_query:
        ambitionbox_url = f"https://www.ambitionbox.com/salaries?company={urllib.parse.quote(comp_query)}&designation={urllib.parse.quote(clean_title)}"
        embed.add_field(
            name="📊 AmbitionBox Salary Estimates",
            value=f"[Check **{comp_query}** Salary Insights on AmbitionBox]({ambitionbox_url})",
            inline=False
        )
    else:
        ambitionbox_url = f"https://www.ambitionbox.com/salaries?designation={urllib.parse.quote(clean_title)}"
        embed.add_field(
            name="📊 AmbitionBox Salary Estimates",
            value=f"[Check **{clean_title}** Salary Insights on AmbitionBox]({ambitionbox_url})",
            inline=False
        )

    embed.add_field(
        name="🔗 Where to Apply",
        value=f"**[👉 Click Here to Open & Apply on {provider_name}]({job.apply_url})**",
        inline=False
    )
    
    if job.company_logo_url:
        embed.set_thumbnail(url=job.company_logo_url)

    embed.set_footer(text=f"Result {current_idx} of {total_count} • Source: {provider_name} • ID: {job.job_id}")
    return embed

def create_job_detail_embed(job: CachedJob) -> discord.Embed:
    """Format clean full job details embed."""
    provider_name = job.provider.replace("_", " ").title()
    embed = discord.Embed(
        title=f"💼 {job.title}",
        url=job.apply_url,
        color=0x2ECC71
    )
    embed.add_field(name="📍 Location", value=f"`{job.location}` {'(Remote 🏠)' if job.is_remote else ''}", inline=True)
    embed.add_field(name="🕒 Employment Type", value=f"`{job.employment_type}`", inline=True)
    
    if job.salary_range and job.salary_range.lower() not in ("competitive", "not disclosed", "none"):
        embed.add_field(name="💰 Disclosed Salary", value=f"`{job.salary_range}`", inline=True)
        
    if job.company and "Live" not in job.company and "Portal" not in job.company:
        embed.add_field(name="🏢 Company", value=f"`{job.company}`", inline=True)

    clean_title = job.title.split("—")[-1].strip() if "—" in job.title else job.title
    comp_query = job.company if (job.company and "Live" not in job.company and "Portal" not in job.company) else ""
    if comp_query:
        ambitionbox_url = f"https://www.ambitionbox.com/salaries?company={urllib.parse.quote(comp_query)}&designation={urllib.parse.quote(clean_title)}"
        embed.add_field(
            name="📊 AmbitionBox Salary Insights",
            value=f"[Check **{comp_query}** Salary Insights on AmbitionBox]({ambitionbox_url})",
            inline=False
        )
    else:
        ambitionbox_url = f"https://www.ambitionbox.com/salaries?designation={urllib.parse.quote(clean_title)}"
        embed.add_field(
            name="📊 AmbitionBox Salary Insights",
            value=f"[Check **{clean_title}** Salary Insights on AmbitionBox]({ambitionbox_url})",
            inline=False
        )

    embed.add_field(
        name="🔗 Direct Application Link",
        value=f"**[👉 Open Direct Application Portal ({provider_name})]({job.apply_url})**",
        inline=False
    )
    embed.set_footer(text=f"Source: {provider_name} • ID: {job.job_id}")
    return embed

def create_resume_review_embed(review: Dict[str, Any], candidate_name: str) -> discord.Embed:
    """Format Gemini AI Resume critique & improvement review embed."""
    score = review.get("ats_score", 70)
    score_color = COLOR_SUCCESS if score >= 80 else COLOR_WARNING if score >= 60 else COLOR_DANGER

    embed = discord.Embed(
        title=f"✨ Google Gemini AI Resume Audit: {candidate_name}",
        description=f"**ATS Compatibility & Impact Score:** `{score}/100`\n"
                    f"**Verdict:** {review.get('summary_verdict', 'Analysis complete.')}",
        color=score_color
    )

    # 1. Strengths
    strengths = review.get("strengths", [])
    if strengths:
        embed.add_field(
            name="🌟 Key Strengths",
            value="\n".join([f"• {s}" for s in strengths[:3]]),
            inline=False
        )

    # 2. What is NOT good / Weaknesses
    flaws = review.get("weaknesses_and_flaws", [])
    if flaws:
        embed.add_field(
            name="⚠️ What Needs Improvement (Critical Flaws)",
            value="\n".join([f"• {w}" for w in flaws[:3]]),
            inline=False
        )

    # 3. Missing Metrics
    metrics = review.get("missing_metrics", [])
    if metrics:
        embed.add_field(
            name="📊 Missing Numbers & Impact Metrics",
            value="\n".join([f"• {m}" for m in metrics[:2]]),
            inline=False
        )

    # 4. Bullet Point Rewrites
    improvements = review.get("bullet_point_improvements", [])
    if improvements:
        first_imp = improvements[0]
        embed.add_field(
            name="💡 AI Recommended Bullet Rewrite (Google XYZ Method)",
            value=f"❌ **Before:** *\"{first_imp.get('original', '')}\"*\n"
                  f"✅ **After:** **\"{first_imp.get('improved', '')}\"**\n"
                  f"🔍 **Why:** {first_imp.get('reason', '')}",
            inline=False
        )

    # 5. Actionable checklist
    recommendations = review.get("actionable_recommendations", [])
    if recommendations:
        embed.add_field(
            name="🚀 Actionable Next Steps",
            value="\n".join([f"1️⃣ {r}" if i==0 else f"2️⃣ {r}" if i==1 else f"3️⃣ {r}" for i, r in enumerate(recommendations[:3])]),
            inline=False
        )

    embed.set_footer(text="Powered by Google Gemini AI • Use /jobs match to find jobs matching your resume")
    return embed

def create_resume_parsed_embed(profile_data: Dict[str, Any], candidate_name: str) -> discord.Embed:
    """Format extracted resume profile embed."""
    embed = discord.Embed(
        title=f"🤖 AI Resume Insights: {candidate_name}",
        description="Extracted key attributes from your uploaded resume:",
        color=COLOR_GEMINI
    )
    embed.add_field(name="🎯 Target Role", value=f"`{profile_data.get('primary_role', 'Software Engineer')}`", inline=True)
    embed.add_field(name="⏳ Experience", value=f"`{profile_data.get('years_of_experience', 0)} years`", inline=True)
    
    skills = profile_data.get("skills", [])
    skill_text = ", ".join([f"`{s}`" for s in skills[:8]]) if skills else "None detected"
    embed.add_field(name="🛠️ Detected Skills", value=skill_text, inline=False)
    
    locations = profile_data.get("suggested_locations", [])
    if locations:
        embed.add_field(name="📍 Suggested Markets", value=", ".join(locations[:4]), inline=False)

    embed.set_footer(text="Run /jobs match to search openings tailored to these skills across LinkedIn & Naukri.")
    return embed

def create_profile_embed(user: UserProfile) -> discord.Embed:
    """Format user profile status embed."""
    embed = discord.Embed(
        title=f"👤 Candidate Profile: {user.full_name or user.username}",
        color=COLOR_PRIMARY
    )
    
    embed.add_field(name="📧 Email", value=f"`{user.email or 'Not configured'}`", inline=True)
    embed.add_field(name="📱 Phone", value=f"`{user.phone or 'Not configured'}`", inline=True)
    embed.add_field(name="📍 Location", value=f"`{user.city or ''}, {user.country or 'Not set'}`", inline=True)
    
    embed.add_field(name="💼 Current Role", value=f"`{user.current_role or 'Not set'}` at `{user.current_company or 'N/A'}`", inline=False)
    embed.add_field(name="⏳ Experience", value=f"`{user.years_of_experience} years`", inline=True)
    embed.add_field(name="⏱️ Notice Period", value=f"`{user.notice_period_days} days`", inline=True)
    embed.add_field(name="🛂 Sponsorship", value=f"`{'Required' if user.requires_sponsorship else 'Not required'}`", inline=True)
    
    resume_status = f"✅ `{user.resume_filename}`" if user.resume_file_path else "❌ No resume uploaded (use `/profile resume`)"
    embed.add_field(name="📄 Resume File", value=resume_status, inline=False)
    
    companies_status = f"🏢 `{user.target_companies}`" if user.target_companies else "⚠️ None configured (use `/profile companies`)"
    embed.add_field(name="🎯 Target Dream Companies", value=companies_status, inline=False)
    
    cookie_status = "✅ Configured (Active)" if user.linkedin_cookie_enc else "⚠️ Not configured (Direct form only)"
    embed.add_field(name="⚡ LinkedIn Session Key", value=cookie_status, inline=False)
    
    embed.set_footer(text="Update your details anytime with `/profile setup` or `/profile companies`.")
    return embed

def create_application_result_embed(result: Dict[str, Any], job: CachedJob, user: UserProfile) -> discord.Embed:
    """Format application confirmation / status embed."""
    status = result.get("status", ApplyStatus.PENDING.value)
    
    if status == ApplyStatus.SUBMITTED.value:
        embed = discord.Embed(
            title="🎉 Application Submitted Successfully!",
            description=f"Your profile and resume were delivered for **{job.title}** at **{job.company}**.",
            color=COLOR_SUCCESS
        )
    elif status == ApplyStatus.MANUAL_REQUIRED.value:
        embed = discord.Embed(
            title="⚠️ Action Required: Complete On Portal",
            description=f"**{result.get('message')}**\n\nClick the link below to finalize your submission on **{job.company}**'s career portal.",
            color=COLOR_WARNING
        )
    else:
        embed = discord.Embed(
            title="❌ Application Failed",
            description=f"Could not automatically apply: **{result.get('message', 'Unknown error')}**",
            color=COLOR_DANGER
        )

    embed.add_field(name="Job Title", value=f"`{job.title}`", inline=True)
    embed.add_field(name="Company", value=f"`{job.company}`", inline=True)
    embed.add_field(name="Apply Mode", value=f"`{job.apply_type}`", inline=True)
    embed.add_field(name="Direct Portal Link", value=f"[Open Application Portal]({job.apply_url})", inline=False)
    
    if result.get("screenshot_path"):
        embed.set_footer(text="Confirmation screenshot attached below.")

    return embed

def create_applications_list_embed(applications: List[JobApplication], user: UserProfile) -> discord.Embed:
    """Format user's application history."""
    embed = discord.Embed(
        title=f"📋 Job Applications History ({len(applications)})",
        description=f"Tracked applications for **{user.full_name or user.username}**:",
        color=COLOR_PRIMARY
    )
    
    if not applications:
        embed.description = "You haven't submitted any job applications yet! Use `/jobs search` or `/jobs match` to find open positions."
        return embed

    for app in applications[:10]:
        status_emoji = "✅" if app.status == ApplyStatus.SUBMITTED.value else "⚠️" if app.status == ApplyStatus.MANUAL_REQUIRED.value else "❌"
        date_str = app.applied_at.strftime("%Y-%m-%d %H:%M") if app.applied_at else "Recently"
        embed.add_field(
            name=f"{status_emoji} {app.job_title} @ {app.company_name}",
            value=f"Status: `{app.status}` • Mode: `{app.apply_type}` • Applied: `{date_str}`\nID: `{app.job_id}`",
            inline=False
        )

    embed.set_footer(text="Showing most recent 10 applications.")
    return embed

def create_help_embed() -> discord.Embed:
    """Format help instructions embed."""
    embed = discord.Embed(
        title="🤖 Discord Job Search & Easy Apply Bot (with Gemini AI & Alerts)",
        description="Search for jobs globally, set automated alerts with user tagging, critique your resume with Gemini AI, and auto-apply directly from Discord.",
        color=COLOR_PRIMARY
    )
    
    embed.add_field(
        name="🔍 Job Search Commands",
        value="• `/jobs search <query> [location] [remote] [type]` - Search live listings (LinkedIn, Naukri, Google Jobs)\n"
              "• `/jobs match` - Auto-match jobs based on your uploaded resume\n"
              "• `/jobs view <job_id>` - View full description, requirements & live links\n"
              "• `/jobs apply <job_id>` - Auto-apply using your stored profile & resume",
        inline=False
    )
    
    embed.add_field(
        name="🔔 Automated Job Alerts",
        value="• `/alerts create <query> [location] [company] [min_salary]` - Get tagged when new jobs appear\n"
              "• `/alerts list` - View your active job alerts\n"
              "• `/alerts delete <alert_id>` - Delete an alert rule",
        inline=False
    )

    embed.add_field(
        name="✨ Gemini AI Resume Commands",
        value="• `/resume review` - Deep AI critique of what's not good in your resume + bullet rewrites\n"
              "• `/resume parse` - Extract skills & role from resume to update your profile automatically",
        inline=False
    )

    embed.add_field(
        name="👤 Profile & Resume Commands",
        value="• `/profile setup` - Set your full name, email, phone, and links\n"
              "• `/profile resume` - Upload your PDF resume for auto-applications & AI review\n"
              "• `/profile details` - Set experience years, notice period, sponsorship\n"
              "• `/profile cookie` - Save LinkedIn session token for Easy Apply\n"
              "• `/profile view` - View your saved candidate profile",
        inline=False
    )

    embed.set_footer(text="Hosted 100% Free on Google Cloud Platform • Gemini AI Enabled")
    return embed
