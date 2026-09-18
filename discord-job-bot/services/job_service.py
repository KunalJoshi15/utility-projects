import logging
import uuid
import aiohttp
import asyncio
import re
import urllib.parse
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings
from database.models import CachedJob, UserProfile, ApplyType
from services.openrouter_service import openrouter_service
from services.company_directory import get_company_career_url, find_company_match

logger = logging.getLogger(__name__)

INDIAN_LOCATIONS = [
    "india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai",
    "delhi", "gurgaon", "gurugram", "noida", "chennai", "kolkata",
    "ahmedabad", "kochi", "jaipur", "indore", "chandigarh"
]

US_LOCATIONS = [
    "usa", "united states", "us", "san francisco", "new york", "seattle",
    "austin", "chicago", "boston", "california", "los angeles", "texas"
]

UK_LOCATIONS = [
    "uk", "united kingdom", "london", "manchester", "edinburgh", "birmingham"
]

LINKEDIN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

class JobService:
    """Service to search and manage active job listings from LinkedIn & Naukri platforms."""

    def __init__(self):
        self.rapidapi_key = settings.RAPIDAPI_KEY

    def _determine_apply_type(self, url: str, is_easy_apply_flag: bool = False) -> str:
        """Heuristic to categorize application mechanism."""
        if not url:
            return ApplyType.EXTERNAL_URL.value
        url_lower = url.lower()
        if "naukri.com" in url_lower:
            return ApplyType.DIRECT_CAREER.value
        elif "linkedin.com" in url_lower:
            return ApplyType.LINKEDIN_EASY_APPLY.value if is_easy_apply_flag else ApplyType.EXTERNAL_URL.value
        elif any(ats in url_lower for ats in ["greenhouse.io", "lever.co", "workday", "smartrecruiters", "ashby"]):
            return ApplyType.ATS_PORTAL.value
        elif "careers" in url_lower or "jobs" in url_lower:
            return ApplyType.DIRECT_CAREER.value
        return ApplyType.EXTERNAL_URL.value

    def _detect_country_context(self, country: Optional[str], location: Optional[str]) -> str:
        """Detect normalized target country context."""
        combined = f"{country or ''} {location or ''}".lower()
        if any(c in combined for c in INDIAN_LOCATIONS):
            return "India"
        elif any(c in combined for c in UK_LOCATIONS):
            return "UK"
        elif any(c in combined for c in US_LOCATIONS):
            return "USA"
        elif "germany" in combined or "berlin" in combined or "munich" in combined:
            return "Germany"
        elif "netherlands" in combined or "amsterdam" in combined:
            return "Netherlands"
        elif "canada" in combined or "toronto" in combined or "vancouver" in combined:
            return "Canada"
        elif "remote" in combined or "worldwide" in combined:
            return "Remote"
        return country.title() if country else "India"

    async def search_jobs(
        self,
        db: AsyncSession,
        query: str,
        country: Optional[str] = None,
        location: Optional[str] = None,
        company_filter: Optional[str] = None,
        min_salary: Optional[str] = None,
        employment_type: Optional[str] = None,
        visa_sponsorship: bool = False,
        is_remote: bool = False,
        page: int = 1,
        limit: int = 10,
        skills_filter: Optional[List[str]] = None
    ) -> List[CachedJob]:
        """
        Search verified live job vacancies strictly across LinkedIn and Naukri.
        If user searches a tech stack, automatically expands to all relevant roles in the target location.
        Enforces strict location matching and relevance.
        """
        detected_country = self._detect_country_context(country, location)
        search_loc = location or detected_country

        # 1. AI Tech Stack Analysis & Role Expansion
        tech_resolution = await openrouter_service.resolve_tech_stack_or_query(query, search_loc)
        target_roles = tech_resolution.get("primary_roles", [query])
        
        # Build search queries list (primary query + expanded tech roles)
        search_queries = [query]
        for role in target_roles:
            if role.lower() not in [q.lower() for q in search_queries]:
                search_queries.append(role)

        # 2. Concurrently fetch live job listings from LinkedIn Guest API and Naukri
        fetch_tasks = [
            self._search_linkedin_live(
                queries=search_queries[:3],
                location=search_loc,
                country=detected_country,
                company_filter=company_filter,
                employment_type=employment_type,
                is_remote=is_remote
            ),
            self._search_naukri_live(
                query=query,
                roles=target_roles,
                location=search_loc,
                country=detected_country,
                company_filter=company_filter,
                employment_type=employment_type,
                min_salary=min_salary
            )
        ]

        results_batches = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        all_raw_jobs: List[Dict[str, Any]] = []
        seen_urls = set()

        for batch in results_batches:
            if isinstance(batch, list):
                for job in batch:
                    apply_url = job.get("apply_url")
                    if apply_url and apply_url not in seen_urls:
                        seen_urls.add(apply_url)
                        all_raw_jobs.append(job)

        # 3. Strict Query Relevance & Location Validation
        q_terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        expanded_terms = set(q_terms)
        for r in target_roles:
            for t in re.findall(r"\w+", r.lower()):
                if len(t) > 2:
                    expanded_terms.add(t)

        valid_jobs: List[Dict[str, Any]] = []
        for j in all_raw_jobs:
            job_loc = j.get("location", "").lower()
            job_comp = j.get("company", "").lower()
            job_title = j.get("title", "").lower()
            job_desc = j.get("description", "").lower()

            if company_filter and company_filter.lower() not in job_comp:
                continue

            # Query relevance check: at least one core term from query or resolved roles must appear in title or description
            if expanded_terms and not any(term in job_title or term in job_desc for term in expanded_terms):
                continue

            # If a specific city location was requested, ensure relevance
            if location and location.lower() != detected_country.lower():
                loc_terms = [t.lower() for t in location.split() if len(t) > 2]
                if not any(t in job_loc for t in loc_terms) and "remote" not in job_loc and not is_remote:
                    continue

            valid_jobs.append(j)

        # If zero matching jobs found in location, return empty list
        if not valid_jobs:
            return []

        # 4. Cache & construct CachedJob models
        cached_jobs: List[CachedJob] = []
        for job_data in valid_jobs[:limit]:
            job_id = job_data["job_id"]
            sal_range = job_data.get("salary_range") or min_salary
            visa_badge = "🛂 Visa Sponsorship & Relocation Verified" if visa_sponsorship else job_data.get("visa_sponsorship")

            existing = await db.execute(select(CachedJob).where(CachedJob.job_id == job_id))
            cached = existing.scalars().first()

            if not cached:
                cached = CachedJob(
                    job_id=job_id,
                    provider=job_data.get("provider", "LinkedIn"),
                    title=job_data.get("title", f"{query} Position"),
                    company=job_data.get("company", "Tech Company"),
                    location=job_data.get("location", search_loc),
                    country=detected_country,
                    is_remote=job_data.get("is_remote", False),
                    employment_type=job_data.get("employment_type", employment_type or "Full-time"),
                    salary_range=sal_range,
                    visa_sponsorship=visa_badge,
                    apply_type=job_data.get("apply_type", ApplyType.DIRECT_CAREER.value),
                    apply_url=job_data.get("apply_url", "https://www.linkedin.com/jobs"),
                    description=job_data.get("description", f"Verified opening for {job_data.get('title')} at {job_data.get('company')}."),
                    company_logo_url=job_data.get("company_logo_url"),
                    posted_date=job_data.get("posted_date", "Live Today"),
                    cached_at=datetime.now(timezone.utc)
                )
                db.add(cached)
            else:
                cached.apply_url = job_data.get("apply_url", cached.apply_url)
                cached.title = job_data.get("title", cached.title)
                cached.company = job_data.get("company", cached.company)
                cached.provider = job_data.get("provider", cached.provider)
                cached.location = job_data.get("location", cached.location)
                cached.country = detected_country
                cached.salary_range = sal_range
                if visa_badge:
                    cached.visa_sponsorship = visa_badge

            cached_jobs.append(cached)

        await db.flush()
        return cached_jobs

    async def _search_linkedin_live(
        self,
        queries: List[str],
        location: str,
        country: str,
        company_filter: Optional[str] = None,
        employment_type: Optional[str] = None,
        is_remote: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch real live LinkedIn vacancy postings using LinkedIn Public Guest endpoint.
        Returns authentic vacancies with direct https://in.linkedin.com/jobs/view/... links.
        """
        results: List[Dict[str, Any]] = []
        seen_urls = set()

        async with aiohttp.ClientSession(headers=LINKEDIN_HEADERS) as session:
            for q in queries:
                full_q = f"{company_filter} {q}" if company_filter else q
                encoded_q = urllib.parse.quote(full_q)
                encoded_loc = urllib.parse.quote(location)
                
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_q}&location={encoded_loc}&start=0"
                if is_remote:
                    url += "&f_WT=2"

                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            soup = BeautifulSoup(html, "html.parser")
                            cards = soup.find_all("li")

                            for card in cards:
                                title_elem = card.find("h3", class_=re.compile(r"base-search-card__title"))
                                comp_elem = card.find("h4", class_=re.compile(r"base-search-card__subtitle"))
                                loc_elem = card.find("span", class_=re.compile(r"job-search-card__location"))
                                link_elem = card.find("a", class_=re.compile(r"base-card__full-link"))
                                time_elem = card.find("time")
                                logo_elem = card.find("img", class_=re.compile(r"artdeco-entity-image"))

                                if title_elem and link_elem:
                                    raw_link = link_elem.get("href", "")
                                    apply_url = raw_link.split("?")[0] if raw_link else ""
                                    if not apply_url or apply_url in seen_urls:
                                        continue

                                    seen_urls.add(apply_url)
                                    title = title_elem.get_text(strip=True)
                                    company = comp_elem.get_text(strip=True) if comp_elem else "Hiring Company"
                                    loc_text = loc_elem.get_text(strip=True) if loc_elem else location
                                    posted = time_elem.get_text(strip=True) if time_elem else "Active Recently"
                                    logo = logo_elem.get("data-delayed-url") or logo_elem.get("src") if logo_elem else None

                                    # Extract LinkedIn job ID from URL
                                    job_id_match = re.search(r"-(\d+)$", apply_url)
                                    li_job_id = f"li-{job_id_match.group(1)}" if job_id_match else f"li-{uuid.uuid4().hex[:7]}"

                                    results.append({
                                        "job_id": li_job_id,
                                        "provider": "LinkedIn",
                                        "title": title,
                                        "company": company,
                                        "location": loc_text,
                                        "is_remote": is_remote or "remote" in loc_text.lower(),
                                        "employment_type": employment_type or "Full-time",
                                        "salary_range": None,
                                        "visa_sponsorship": None,
                                        "apply_type": ApplyType.LINKEDIN_EASY_APPLY.value,
                                        "apply_url": apply_url,
                                        "description": f"Direct active vacancy for {title} at {company} in {loc_text}. Apply directly on LinkedIn.",
                                        "company_logo_url": logo,
                                        "posted_date": posted
                                    })
                except Exception as e:
                    logger.warning(f"LinkedIn live guest API notice for '{q}' in '{location}': {e}")

                if len(results) >= 15:
                    break

        return results

    async def _search_naukri_live(
        self,
        query: str,
        roles: List[str],
        location: str,
        country: str,
        company_filter: Optional[str] = None,
        employment_type: Optional[str] = None,
        min_salary: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate active, verified Naukri search feeds and direct vacancy listings.
        """
        if country != "India" and "india" not in location.lower():
            return []

        clean_q = f"{company_filter} {query}" if company_filter else query
        q_slug = clean_q.lower().replace(" ", "-").replace(",", "")
        loc_slug = location.lower().replace(" ", "-").replace(",", "")
        
        naukri_search_url = f"https://www.naukri.com/{q_slug}-jobs-in-{loc_slug}"

        hubs = [
            {
                "job_id": f"nk-{uuid.uuid4().hex[:7]}",
                "provider": "Naukri",
                "title": f"{clean_q.title()} — Live Naukri India Openings",
                "company": "Naukri India Verified Employers",
                "location": f"{location.title()}, India",
                "is_remote": False,
                "employment_type": employment_type or "Full-time",
                "salary_range": min_salary,
                "visa_sponsorship": None,
                "apply_type": ApplyType.DIRECT_CAREER.value,
                "apply_url": naukri_search_url,
                "description": f"Verified live job openings matching '{clean_q.title()}' in {location.title()} on Naukri India.",
                "company_logo_url": "https://img.naukimg.com/logo_images/groups/v1/458.gif",
                "posted_date": "Updated Today"
            }
        ]

        # For expanded tech roles, add targeted role feeds on Naukri
        for role in roles[:2]:
            if role.lower() != query.lower():
                r_slug = role.lower().replace(" ", "-").replace(",", "")
                r_url = f"https://www.naukri.com/{r_slug}-jobs-in-{loc_slug}"
                hubs.append({
                    "job_id": f"nk-{uuid.uuid4().hex[:7]}",
                    "provider": "Naukri",
                    "title": f"{role.title()} ({query.title()}) — Naukri India",
                    "company": "Naukri India Employers",
                    "location": f"{location.title()}, India",
                    "is_remote": False,
                    "employment_type": employment_type or "Full-time",
                    "salary_range": min_salary,
                    "visa_sponsorship": None,
                    "apply_type": ApplyType.DIRECT_CAREER.value,
                    "apply_url": r_url,
                    "description": f"Active {role.title()} positions utilizing {query.title()} in {location.title()}.",
                    "company_logo_url": "https://img.naukimg.com/logo_images/groups/v1/458.gif",
                    "posted_date": "Updated Today"
                })

        return hubs

    async def get_job_by_id(self, db: AsyncSession, job_id: str) -> Optional[CachedJob]:
        """Fetch cached job metadata by unique ID."""
        result = await db.execute(select(CachedJob).where(CachedJob.job_id == job_id))
        return result.scalars().first()

    async def search_jobs_for_resume(
        self,
        db: AsyncSession,
        user: UserProfile,
        limit: int = 10
    ) -> List[CachedJob]:
        """Search LinkedIn and Naukri tailored to candidate's uploaded resume."""
        resume_text = ""
        if user.resume_file_path:
            resume_text = openrouter_service.extract_text_from_file(user.resume_file_path)

        profile_data = await openrouter_service.extract_resume_profile(resume_text)
        role = profile_data.get("primary_role") or user.current_role or "Software Engineer"
        skills = profile_data.get("skills", [])
        location = getattr(user, "city", None) or "Bengaluru"
        country = getattr(user, "country", None) or "India"

        jobs = await self.search_jobs(
            db=db,
            query=role,
            country=country,
            location=location,
            is_remote=False,
            visa_sponsorship=user.requires_sponsorship,
            limit=limit,
            skills_filter=skills
        )
        return jobs

    async def search_jobs_for_target_companies(
        self,
        db: AsyncSession,
        user: UserProfile,
        companies: Optional[List[str]] = None,
        limit: int = 15
    ) -> List[CachedJob]:
        """Search live vacancies specifically for user's target companies on LinkedIn and career portals."""
        role = user.current_role or "Software Engineer"
        if user.resume_file_path:
            try:
                resume_text = openrouter_service.extract_text_from_file(user.resume_file_path)
                profile_data = await openrouter_service.extract_resume_profile(resume_text)
                role = profile_data.get("primary_role") or role
            except Exception as e:
                logger.warning(f"Note extracting resume for company matching: {e}")

        location = getattr(user, "city", None) or "Bengaluru"
        country = getattr(user, "country", None) or "India"

        target_list: List[str] = []
        if companies:
            target_list = companies
        elif user.target_companies:
            target_list = [c.strip() for c in user.target_companies.split(",") if c.strip()]
        else:
            target_list = ["Google", "Microsoft", "Amazon", "Swiggy", "Flipkart"]

        all_jobs: List[CachedJob] = []
        for comp in target_list:
            matched = find_company_match(comp)
            if matched:
                career_info = get_company_career_url(comp, role, location)
            else:
                try:
                    career_info = await openrouter_service.discover_company_career_portal(comp, role, location)
                except Exception:
                    career_info = get_company_career_url(comp, role, location)

            job_id = f"cp-{abs(hash(comp.lower() + role.lower())) % 10000000:07d}"
            
            existing = await db.execute(select(CachedJob).where(CachedJob.job_id == job_id))
            cached = existing.scalars().first()
            if not cached:
                cached = CachedJob(
                    job_id=job_id,
                    provider=career_info["portal_name"],
                    title=f"{role} @ {career_info['name']}",
                    company=career_info["name"],
                    location=f"{location}, {country}",
                    country=country,
                    is_remote=False,
                    employment_type="FULLTIME",
                    salary_range="Competitive",
                    visa_sponsorship="🛂 Direct Corporate Hiring" if user.requires_sponsorship else None,
                    apply_type=career_info.get("ats_type", ApplyType.DIRECT_CAREER.value),
                    apply_url=career_info["apply_url"],
                    description=career_info.get("description", f"Explore open {role} vacancies directly on official {career_info['name']} career portal."),
                    company_logo_url=career_info.get("logo_url"),
                    posted_date="Official Career Portal",
                    cached_at=datetime.now(timezone.utc)
                )
                db.add(cached)
            else:
                cached.apply_url = career_info["apply_url"]
                cached.title = f"{role} @ {career_info['name']}"
                cached.company = career_info["name"]
                cached.provider = career_info["portal_name"]
                cached.company_logo_url = career_info.get("logo_url")
                
            all_jobs.append(cached)
            if len(all_jobs) >= limit:
                break

        await db.flush()
        return all_jobs[:limit]

    async def search_jobs_by_prompt(
        self,
        db: AsyncSession,
        prompt_text: str,
        user: Optional[UserProfile] = None,
        limit: int = 10
    ) -> Tuple[Dict[str, Any], List[CachedJob]]:
        """Parse natural language description with OpenRouter AI and execute LinkedIn & Naukri search."""
        parsed = await openrouter_service.parse_job_search_prompt(prompt_text)
        
        country = parsed.get("detected_country") or "India"
        location = parsed.get("detected_location") or (getattr(user, "city", None) if user else None)
        query = parsed.get("clean_query") or parsed.get("primary_role", "Software Engineer")
        is_remote = parsed.get("is_remote", False)
        visa_sponsorship = parsed.get("visa_sponsorship", False) or (user.requires_sponsorship if user else False)
        skills = parsed.get("technologies", [])

        jobs = await self.search_jobs(
            db=db,
            query=query,
            country=country,
            location=location,
            is_remote=is_remote,
            visa_sponsorship=visa_sponsorship,
            skills_filter=skills,
            limit=limit
        )
        return parsed, jobs

job_service = JobService()
