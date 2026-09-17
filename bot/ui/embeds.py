import discord
import urllib.parse
from typing import List, Dict, Any, Optional
from database.models import CachedJob, UserProfile, JobApplication, ApplyType, ApplyStatus
from services.salary_service import salary_service

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

    if job.visa_sponsorship:
        embed.add_field(name="🛂 Visa / Relocation", value=f"`{job.visa_sponsorship}`", inline=True)

    # AmbitionBox & Glassdoor salary estimation links & similar roles
    benchmarks = salary_service.get_salary_benchmarks(job.title, job.company, job.country)
    ab = benchmarks["ambitionbox"]
    gd = benchmarks["glassdoor"]
    comp = benchmarks["company"]
    clean_title = benchmarks["role"]
    
    benchmark_lines = []
    if comp:
        benchmark_lines.append(f"• 🏢 **{comp} Pay:** [AmbitionBox]({ab['company_role_url']}) • [Glassdoor]({gd['company_role_url']}) • [Levels.fyi]({benchmarks['levels_fyi_url']})")
    
    benchmark_lines.append(f"• 🌐 **Market Benchmark ({clean_title}):** [AmbitionBox]({ab['market_role_url']}) • [Glassdoor]({gd['market_role_url']})")
    
    # Similar roles
    sim_ab_links = [f"[{s['role']}]({s['url']})" for s in ab["similar_roles"][:3]]
    if sim_ab_links:
        benchmark_lines.append("• 👥 **Similar Roles:** " + " • ".join(sim_ab_links))

    embed.add_field(
        name="📊 Market Salary Benchmarks (AmbitionBox & Glassdoor)",
        value="\n".join(benchmark_lines),
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

    if job.visa_sponsorship:
        embed.add_field(name="🛂 Visa / Relocation", value=f"`{job.visa_sponsorship}`", inline=True)

    benchmarks = salary_service.get_salary_benchmarks(job.title, job.company, job.country)
    ab = benchmarks["ambitionbox"]
    gd = benchmarks["glassdoor"]
    comp = benchmarks["company"]
    clean_title = benchmarks["role"]
    
    benchmark_lines = []
    if comp:
        benchmark_lines.append(f"• 🏢 **{comp} Compensation:** [AmbitionBox]({ab['company_role_url']}) • [Glassdoor]({gd['company_role_url']}) • [Levels.fyi]({benchmarks['levels_fyi_url']})")
    benchmark_lines.append(f"• 🌐 **Industry Benchmark ({clean_title}):** [AmbitionBox]({ab['market_role_url']}) • [Glassdoor]({gd['market_role_url']})")
    
    sim_ab_links = [f"[{s['role']}]({s['url']})" for s in ab["similar_roles"][:4]]
    if sim_ab_links:
        benchmark_lines.append("• 👥 **Compare Similar Roles:** " + " • ".join(sim_ab_links))

    embed.add_field(
        name="📊 Market Salary Benchmarks (AmbitionBox & Glassdoor)",
        value="\n".join(benchmark_lines),
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

def create_salary_card_embed(benchmarks: Dict[str, Any]) -> discord.Embed:
    """Format full salary intelligence and benchmark embed for a role and company."""
    role = benchmarks["role"]
    comp = benchmarks.get("company")
    loc = benchmarks.get("location", "India")
    ab = benchmarks["ambitionbox"]
    gd = benchmarks["glassdoor"]

    title_text = f"💰 Salary Intelligence: {role}"
    if comp:
        title_text += f" @ {comp}"

    embed = discord.Embed(
        title=title_text,
        description=f"Authentic market compensation data & crowd-sourced paygrades for **{loc}**.",
        color=COLOR_PRIMARY
    )

    if comp:
        comp_links = [
            f"• [🏢 **{comp} {role} Salaries on AmbitionBox**]({ab['company_role_url']})",
            f"• [🏢 **{comp} {role} Salaries on Glassdoor**]({gd['company_role_url']})",
            f"• [📈 **All {comp} Paygrades Overview**]({ab['company_all_url']})",
            f"• [⭐ **{comp} Reviews & Culture**]({ab['company_reviews_url']})",
            f"• [📊 **Levels.fyi Tech Compensation**]({benchmarks['levels_fyi_url']})"
        ]
        embed.add_field(
            name=f"🏢 {comp} Direct Compensation",
            value="\n".join(comp_links),
            inline=False
        )

    # Market Wide Benchmark
    market_links = [
        f"• [🌐 **AmbitionBox Market Salaries for {role}**]({ab['market_role_url']})",
        f"• [🌐 **Glassdoor Market Salaries for {role}**]({gd['market_role_url']})"
    ]
    embed.add_field(
        name=f"🌐 Market Average ({role})",
        value="\n".join(market_links),
        inline=False
    )

    # Similar & Adjacent Roles Benchmarks
    sim_lines = []
    for s_ab, s_gd in zip(ab["similar_roles"], gd["similar_roles"]):
        sim_lines.append(f"• **{s_ab['role']}:** [AmbitionBox]({s_ab['url']}) • [Glassdoor]({s_gd['url']})")

    if sim_lines:
        embed.add_field(
            name="👥 Similar & Adjacent Roles Benchmarks",
            value="\n".join(sim_lines),
            inline=False
        )

    embed.set_footer(text="Data source: AmbitionBox & Glassdoor • No synthetic / fabricated paygrades.")
    return embed

def create_salary_comparison_embed(comparison: Dict[str, Any]) -> discord.Embed:
    """Format side-by-side salary comparison embed across dream companies."""
    role = comparison["role"]
    companies = comparison["companies"]

    embed = discord.Embed(
        title=f"📊 Dream Companies Salary Comparison: {role}",
        description="Side-by-side authentic paygrade intelligence across your target companies:",
        color=COLOR_PRIMARY
    )

    for c in companies:
        c_name = c["company"]
        links = f"• [AmbitionBox]({c['ambitionbox_url']}) • [Glassdoor]({c['glassdoor_url']}) • [Levels.fyi]({c['levels_url']})"
        embed.add_field(
            name=f"🏢 {c_name}",
            value=links,
            inline=True
        )

    embed.add_field(
        name="🌐 Industry Market Baseline",
        value=f"• [AmbitionBox {role} Average]({comparison['market_ambitionbox']})\n• [Glassdoor {role} Average]({comparison['market_glassdoor']})",
        inline=False
    )

    embed.set_footer(text="Data source: AmbitionBox & Glassdoor • Use /profile companies to manage targets.")
    return embed

def create_visa_directory_embed(country_name: str, dir_data: Dict[str, Any]) -> discord.Embed:
    """Format verified visa-sponsoring employers directory embed for a country."""
    flag = dir_data.get("flag", "🌍")
    region = dir_data.get("region", country_name)
    program = dir_data.get("visa_program", "Work Visa / Permanent Residency")
    threshold = dir_data.get("tech_salary_threshold", "Standard going rate")
    reg_url = dir_data.get("official_register_url", "https://google.com")

    embed = discord.Embed(
        title=f"{flag} Verified Visa Sponsorship Directory: {region}",
        description=f"**Visa Scheme:** {program}\n"
                    f"**Tech Benchmark / Salary Threshold:** `{threshold}`\n"
                    f"**Official Government Register:** [View Official Register & Regulations]({reg_url})",
        color=0x3498DB
    )

    # Top Verified Sponsoring Employers
    sponsors = dir_data.get("top_sponsors", [])
    if sponsors:
        sponsor_lines = []
        for s in sponsors[:8]:
            sponsor_lines.append(f"• [**{s['name']}**]({s['career_url']}) — *{s['notes']}*")
        embed.add_field(
            name="🏢 Top Verified Employers Actively Sponsoring",
            value="\n".join(sponsor_lines),
            inline=False
        )

    # Dedicated Relocation & Visa Job Boards
    boards = dir_data.get("job_boards", [])
    if boards:
        board_lines = [f"• [**{b['name']}**]({b['url']})" for b in boards]
        embed.add_field(
            name="🌐 International Relocation Job Feeds",
            value="\n".join(board_lines),
            inline=False
        )

    embed.set_footer(text="Data strictly verified via official government registers • Run /visa jobs to search openings.")
    return embed

def create_visa_jobs_search_embed(search_data: Dict[str, Any]) -> discord.Embed:
    """Format visa sponsorship job search aggregator embed."""
    role = search_data["role"]
    country = search_data["country"]
    country_info = search_data.get("country_info", {})
    flag = country_info.get("flag", "🌍")
    feeds = search_data["feeds"]

    embed = discord.Embed(
        title=f"🛂 International Visa Sponsored Openings: {role} ({flag} {country})",
        description=f"Curated live destination feeds for international candidates seeking relocation & visa sponsorship in **{country}**:",
        color=0x2ECC71
    )

    feed_lines = [
        f"• [✈️ **Relocate.me Openings ({role} in {country})**]({feeds['relocate_me']})",
        f"• [💼 **LinkedIn Visa Sponsorship Filter**]({feeds['linkedin_visa']})",
        f"• [🇪🇺 **Landing.jobs Relocation & Visa Feed**]({feeds['landing_jobs']})",
        f"• [🔍 **Indeed International Visa Feed**]({feeds['indeed_visa']})",
        f"• [🌐 **Google Jobs International Visa Feed**]({feeds['google_jobs_visa']})",
        f"• [📊 **Levels.fyi H-1B / Visa Compensation**]({feeds['levels_h1b']})"
    ]
    embed.add_field(
        name="🔗 Verified Visa & Relocation Job Feeds",
        value="\n".join(feed_lines),
        inline=False
    )

    top_sponsors = search_data.get("top_sponsors", [])
    if top_sponsors:
        s_lines = [f"• [**{s['name']}**]({s['career_url']}) (*{s['notes']}*)" for s in top_sponsors[:5]]
        embed.add_field(
            name=f"🏢 Top Employers in {country} with Active Sponsorship",
            value="\n".join(s_lines),
            inline=False
        )

    embed.set_footer(text="Verified genuine international portals • No misleading visa claims.")
    return embed

def create_visa_company_intel_embed(intel: Dict[str, Any]) -> discord.Embed:
    """Format company visa sponsorship track record & registry checker embed."""
    comp = intel["company"]
    is_verified = intel["is_verified_in_directory"]
    tracks = intel.get("verified_sponsorship_tracks", [])
    reg = intel["registry_links"]

    status_badge = "✅ Verified International Sponsor" if is_verified else "ℹ️ Check Public Sponsor Registries"

    embed = discord.Embed(
        title=f"🛂 Visa Sponsorship Intelligence: {comp}",
        description=f"**Status:** `{status_badge}`",
        color=COLOR_SUCCESS if is_verified else COLOR_PRIMARY
    )

    if tracks:
        for t in tracks[:3]:
            track_text = (
                f"**Country/Hub:** {t['flag']} {t['country']}\n"
                f"**Visa Scheme:** {t['visa_program']}\n"
                f"**Details:** {t['notes']}\n"
                f"**Portal:** [Direct Careers Page]({t['career_url']}) • [Government Register]({t['official_register_url']})"
            )
            embed.add_field(name=f"📍 {t['flag']} {t['country']} Sponsorship Track", value=track_text, inline=False)

    checker_lines = [
        f"• [🇬🇧 **UK Home Office Register of Licensed Sponsors**]({reg['uk_home_office']})",
        f"• [🇺🇸 **Levels.fyi H-1B & Visa Salary Database**]({reg['levels_fyi']})",
        f"• [📊 **MyVisaJobs H-1B & Green Card Records**]({reg['myvisajobs']})",
        f"• [💼 **LinkedIn {comp} Visa Job Postings**]({reg['linkedin_visa_jobs']})"
    ]
    embed.add_field(
        name="🔍 Official Registry & Transparency Checkers",
        value="\n".join(checker_lines),
        inline=False
    )

    embed.set_footer(text="Always confirm specific role eligibility on the employer's official job description.")
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
        value="• `/jobs search <query> [location] [type] [salary] [company] [visa_sponsorship]` - Search live listings (LinkedIn, Naukri, Relocate.me, Google Jobs)\n"
              "• `/jobs match` - Auto-match jobs based on your uploaded resume\n"
              "• `/jobs companies [names]` - View open vacancies across your target dream companies\n"
              "• `/jobs view <job_id>` - View full description, requirements & live links\n"
              "• `/jobs apply <job_id>` - Auto-apply using your stored profile & resume",
        inline=False
    )
    
    embed.add_field(
        name="🛂 Visa Sponsorship & Relocation Commands",
        value="• `/visa companies [country]` - Browse top verified employers offering visa sponsorship in Germany, UK, Netherlands, Canada, USA, SG, UAE\n"
              "• `/visa jobs <role> [country]` - Search verified relocation & visa openings across Relocate.me, Landing.jobs & LinkedIn\n"
              "• `/visa policy <company>` - Check official visa sponsorship track record & government registry status",
        inline=False
    )

    embed.add_field(
        name="💰 Salary & Market Benchmark Commands",
        value="• `/salary check <role> [company] [location]` - Look up authentic AmbitionBox & Glassdoor benchmarks for role & similar roles\n"
              "• `/salary compare <role> [custom_companies]` - Compare paygrades across your dream companies",
        inline=False
    )

    embed.add_field(
        name="🔔 Automated Job Alerts",
        value="• `/alerts create <query> [location] [company] [min_salary] [visa_sponsorship]` - Get tagged when new jobs appear\n"
              "• `/alerts companies [role] [min_salary]` - Batch create 24/7 alerts for all your dream companies\n"
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
        value="• `/profile setup` - Set your full name, email, phone, and location\n"
              "• `/profile companies <names>` - Save your target dream companies (Google, Microsoft, etc.)\n"
              "• `/profile resume` - Upload your PDF resume for auto-applications & AI review\n"
              "• `/profile details` - Set experience years, notice period, sponsorship\n"
              "• `/profile cookie` - Save LinkedIn session token for Easy Apply\n"
              "• `/profile view` - View your saved candidate profile",
        inline=False
    )

    embed.set_footer(text="Hosted 100% Free on Google Cloud Platform • Gemini AI Enabled")
    return embed
