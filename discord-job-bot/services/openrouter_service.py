import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiohttp
from config.settings import settings

logger = logging.getLogger(__name__)

class OpenRouterAIService:
    """
    Modular OpenRouter AI Service for Job Search, Resume Review & Talent Intelligence.
    Easily configurable with any OpenRouter model (including free tier models).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None
    ):
        self.api_key = api_key or getattr(settings, "OPENROUTER_API_KEY", None)
        self.base_url = (base_url or getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")).rstrip('/')
        self.default_model = default_model or getattr(settings, "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
        self.site_url = getattr(settings, "OPENROUTER_SITE_URL", "https://discord-job-bot.local")
        self.app_name = getattr(settings, "OPENROUTER_APP_NAME", "Discord Job Bot")

    async def call_chat_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout_seconds: int = 5
    ) -> Optional[str]:
        """
        Send prompt to OpenRouter OpenAI-compatible chat completions endpoint.
        Automatically falls back to openrouter/free or heuristic rules.
        Returns the raw message content string or None on failure.
        """
        if not self.api_key or self.api_key.startswith("your_"):
            logger.debug("OpenRouter API key is not configured or is placeholder. Using heuristic fallback.")
            return None

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

        # List of models to try in sequence
        models_to_try = [
            model or self.default_model,
            "openrouter/free"
        ]
        # Remove duplicates while preserving order
        unique_models = []
        for m in models_to_try:
            if m and m not in unique_models:
                unique_models.append(m)

        for current_model in unique_models:
            payload: Dict[str, Any] = {
                "model": current_model,
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
                            logger.warning(f"Unexpected response structure from OpenRouter ({current_model}): {data}")
                        elif resp.status == 429:
                            logger.info(f"OpenRouter model '{current_model}' rate limited (429), trying next fallback model...")
                            continue
                        else:
                            error_text = await resp.text()
                            logger.warning(f"OpenRouter model '{current_model}' returned {resp.status}: {error_text}")
            except Exception as e:
                logger.warning(f"OpenRouter query failed for model '{current_model}': {e}")

        return None

    async def _call_ai_model(self, prompt: str) -> Optional[str]:
        """Backward compatibility alias for older service wrappers."""
        return await self.call_chat_completion(prompt)

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

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or text resume file."""
        if not file_path or not os.path.exists(file_path):
            return ""

        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
                return text.strip()
            except Exception as e:
                logger.error(f"Error extracting text from PDF {file_path}: {e}")
                return ""
        else:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading text file {file_path}: {e}")
                return ""

    async def analyze_resume(self, resume_text: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Deep critique and improvement audit using OpenRouter AI model."""
        if not resume_text or len(resume_text.strip()) < 50:
            return {
                "ats_score": 30,
                "summary_verdict": "Resume content is too short or could not be fully extracted.",
                "strengths": ["Document uploaded"],
                "weaknesses_and_flaws": ["Insufficient text content to perform full ATS screening."],
                "missing_metrics": ["Add quantifiable metrics (e.g. '% latency reduced', '$ revenue generated')."],
                "bullet_point_improvements": [],
                "actionable_recommendations": ["Re-upload a detailed PDF resume with complete work experience."]
            }

        prompt = (
            "You are an elite Tech Career Coach and Senior Technical Recruiter. "
            "Critique the following candidate resume thoroughly. Identify what is NOT good, what is weak, "
            "what is missing, and how to improve it.\n\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "ats_score": <int between 0 and 100>,\n'
            '  "summary_verdict": "<2 sentence honest executive summary>",\n'
            '  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],\n'
            '  "weaknesses_and_flaws": ["<weak area 1>", "<weak area 2>", "<weak area 3>"],\n'
            '  "missing_metrics": ["<missing metric / numbers example 1>", "<missing metric 2>"],\n'
            '  "bullet_point_improvements": [\n'
            '    {\n'
            '      "original": "<exact weak bullet from resume>",\n'
            '      "improved": "<high-impact rewrite using Google XYZ or STAR method with metrics>",\n'
            '      "reason": "<why the rewrite is much stronger>"\n'
            '    }\n'
            '  ],\n'
            '  "actionable_recommendations": ["<recommendation 1>", "<recommendation 2>", "<recommendation 3>"]\n'
            "}\n\n"
            f"Candidate Resume Content:\n{resume_text[:6000]}"
        )

        raw_response = await self.call_chat_completion(prompt, model=model)
        if raw_response:
            parsed = self._clean_and_parse_json(raw_response)
            if isinstance(parsed, dict) and "ats_score" in parsed:
                return parsed

        # Intelligent heuristic fallback analysis
        return self._heuristic_resume_analysis(resume_text)

    async def extract_resume_profile(self, resume_text: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Extract candidate skills, target roles, and experience from resume text."""
        if resume_text and len(resume_text.strip()) >= 20:
            prompt = (
                "Extract structured candidate profile information from this resume. "
                "Return ONLY a valid JSON object matching this schema:\n"
                "{\n"
                '  "primary_role": "<e.g. Senior Backend Engineer>",\n'
                '  "skills": ["<skill1>", "<skill2>", "<skill3>", "<skill4>", "<skill5>"],\n'
                '  "years_of_experience": <integer>,\n'
                '  "suggested_locations": ["<location1>", "<location2>"],\n'
                '  "companies": ["<company1>", "<company2>"]\n'
                "}\n\n"
                f"Resume:\n{resume_text[:4000]}"
            )
            raw_response = await self.call_chat_completion(prompt, model=model)
            if raw_response:
                parsed = self._clean_and_parse_json(raw_response)
                if isinstance(parsed, dict) and "skills" in parsed:
                    return parsed

        # Heuristic profile extractor
        return self._heuristic_extract_profile(resume_text)

    def _heuristic_resume_analysis(self, text: str) -> Dict[str, Any]:
        """Rule-based ATS and impact analysis when API key is not yet set."""
        text_lower = text.lower()
        score = 65

        # Check for numbers/metrics
        numbers_count = len(re.findall(r"\b\d+[%kM$+]?", text))
        weaknesses = []
        missing_metrics = []
        strengths = []

        if numbers_count < 5:
            score -= 15
            weaknesses.append("Lack of quantifiable business impact (very few metrics, percentages, or numbers found).")
            missing_metrics.append("Quantify accomplishments (e.g., 'Improved API throughput by 42%', 'Reduced cloud costs by $18K/yr').")
        else:
            strengths.append("Good inclusion of quantifiable achievements and data metrics.")
            score += 10

        # Action verbs check
        action_verbs = ["architected", "engineered", "spearheaded", "accelerated", "optimized", "reduced", "delivered", "scaled"]
        found_verbs = [v for v in action_verbs if v in text_lower]
        if len(found_verbs) < 3:
            weaknesses.append("Uses passive phrasing (e.g. 'Responsible for...', 'Worked on...') instead of strong action verbs.")
            weaknesses.append("Need stronger power verbs at the beginning of each bullet point.")
        else:
            strengths.append(f"Effective use of power action verbs: {', '.join(found_verbs[:4])}.")

        # Tech keywords
        skills_found = [s for s in ["python", "java", "docker", "kubernetes", "aws", "gcp", "react", "sql", "ci/cd", "microservices"] if s in text_lower]
        if skills_found:
            strengths.append(f"Identified core technical competencies: {', '.join(skills_found[:5])}.")

        score = max(35, min(95, score))

        return {
            "ats_score": score,
            "summary_verdict": f"Candidate profile demonstrates technical foundation, but needs higher metric density and ATS optimization to stand out.",
            "strengths": strengths or ["Clear chronological formatting", "Recognizable tech stack"],
            "weaknesses_and_flaws": weaknesses or ["Bullet points focus on duties rather than business outcomes.", "Missing specific tech versions and frameworks in experience section."],
            "missing_metrics": missing_metrics or ["Add scale indicators (e.g., QPS, team size, database volume, test coverage %)."],
            "bullet_point_improvements": [
                {
                    "original": "Responsible for developing backend APIs and fixing bugs.",
                    "improved": "Architected 12+ RESTful microservices using Python & FastAPI, reducing endpoint latency by 35% across 2M daily requests.",
                    "reason": "Replaces passive duty description with specific technologies, scale metrics, and quantifiable impact."
                }
            ],
            "actionable_recommendations": [
                "Adopt Google's X-Y-Z formula: Accomplished [X] as measured by [Y], by doing [Z].",
                "Ensure every work experience bullet point begins with a past-tense power action verb.",
                "Incorporate target job description keywords into your Skills & Experience sections for higher ATS match ranking."
            ]
        }

    def _heuristic_extract_profile(self, text: str) -> Dict[str, Any]:
        """Extract basic profile tokens via regex."""
        text_lower = text.lower()
        skills = []
        popular_skills = [
            "Python", "Java", "Go", "JavaScript", "TypeScript", "React", "Node.js",
            "SQL", "PostgreSQL", "Docker", "Kubernetes", "AWS", "GCP", "FastAPI",
            "Django", "Spring Boot", "Microservices", "CI/CD", "Git", "Redis"
        ]
        for skill in popular_skills:
            if skill.lower() in text_lower:
                skills.append(skill)

        # Guess role
        role = "Software Engineer"
        if "frontend" in text_lower or "react" in text_lower and "backend" not in text_lower:
            role = "Frontend Engineer"
        elif "data engineer" in text_lower or "spark" in text_lower:
            role = "Data Engineer"
        elif "devops" in text_lower or "sre" in text_lower or "kubernetes" in text_lower:
            role = "DevOps / Cloud Engineer"
        elif "full stack" in text_lower or "fullstack" in text_lower:
            role = "Full Stack Engineer"

        return {
            "primary_role": role,
            "skills": skills[:8] or ["Python", "SQL", "Cloud", "Git"],
            "years_of_experience": 3,
            "suggested_locations": ["Remote", "Bengaluru", "San Francisco", "Hyderabad", "London"],
            "companies": []
        }

    async def parse_job_search_prompt(self, prompt_text: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Convert a user's natural language description/prompt into structured search parameters."""
        if not prompt_text or len(prompt_text.strip()) < 5:
            return {
                "primary_role": "Software Engineer",
                "technologies": ["Python", "SQL"],
                "seniority": "Mid-Level",
                "clean_query": "Software Engineer",
                "detected_location": None,
                "detected_country": "India",
                "is_remote": False,
                "visa_sponsorship": False,
                "summary_intent": "General software engineering openings."
            }

        prompt = (
            "You are a talent search AI. Convert the following candidate job search prompt / description "
            "into structured technical search parameters. Extract the core role, technologies, location, "
            "remote preference, and visa requirement.\n\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "primary_role": "<e.g. Backend Engineer, Frontend Developer, Data Engineer>",\n'
            '  "technologies": ["<tech 1>", "<tech 2>", "<tech 3>"],\n'
            '  "seniority": "<Junior / Mid / Senior / Lead>",\n'
            '  "clean_query": "<concise search query term with role and top 2 key tech>",\n'
            '  "detected_location": "<city name if mentioned, otherwise null>",\n'
            '  "detected_country": "<country name if mentioned or implied (e.g. India, Germany, UK, USA, Remote)>",\n'
            '  "is_remote": <boolean>,\n'
            '  "visa_sponsorship": <boolean>,\n'
            '  "summary_intent": "<1 sentence clean summary of what user wants>"\n'
            "}\n\n"
            f"User Prompt:\n{prompt_text[:2000]}"
        )
        raw_response = await self.call_chat_completion(prompt, model=model)
        if raw_response:
            parsed = self._clean_and_parse_json(raw_response)
            if isinstance(parsed, dict) and "primary_role" in parsed:
                return parsed

        # Heuristic prompt parser
        return self._heuristic_parse_prompt(prompt_text)

    def _heuristic_parse_prompt(self, text: str) -> Dict[str, Any]:
        """Rule-based natural language job prompt parser."""
        text_lower = text.lower()
        popular_tech = [
            "Python", "Java", "Go", "Golang", "JavaScript", "TypeScript", "React", "Node.js", "Next.js",
            "C++", "Rust", "Kafka", "Kubernetes", "Docker", "AWS", "GCP", "FastAPI", "Django",
            "Spring Boot", "Microservices", "PostgreSQL", "MongoDB", "Redis", "GraphQL", "Flutter"
        ]
        found_tech = [tech for tech in popular_tech if tech.lower() in text_lower]

        # Seniority
        seniority = "Mid-Level"
        if any(w in text_lower for w in ["lead", "principal", "architect", "staff"]):
            seniority = "Lead"
        elif any(w in text_lower for w in ["senior", "sr", "experienced", "5+ years", "4+ years"]):
            seniority = "Senior"
        elif any(w in text_lower for w in ["junior", "jr", "entry", "fresher", "intern"]):
            seniority = "Junior / Intern"

        # Role
        role = "Software Engineer"
        if "backend" in text_lower:
            role = "Backend Engineer"
        elif "frontend" in text_lower or "react" in text_lower or "ui" in text_lower:
            role = "Frontend Engineer"
        elif "fullstack" in text_lower or "full stack" in text_lower:
            role = "Full Stack Engineer"
        elif "data engineer" in text_lower:
            role = "Data Engineer"
        elif "data scientist" in text_lower or "machine learning" in text_lower or "ai" in text_lower:
            role = "Machine Learning / Data Scientist"
        elif "devops" in text_lower or "sre" in text_lower or "cloud" in text_lower:
            role = "DevOps / Cloud Engineer"

        # Location & country
        is_remote = "remote" in text_lower or "wfh" in text_lower
        detected_loc = None
        detected_country = "India"

        for city in ["bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon", "chennai"]:
            if city in text_lower:
                detected_loc = city.title()
                detected_country = "India"
                break

        for cnt in ["germany", "berlin", "uk", "london", "netherlands", "amsterdam", "canada", "toronto", "usa", "us"]:
            if cnt in text_lower:
                if cnt in ["germany", "berlin"]:
                    detected_country = "Germany"
                elif cnt in ["uk", "london"]:
                    detected_country = "UK"
                elif cnt in ["netherlands", "amsterdam"]:
                    detected_country = "Netherlands"
                elif cnt in ["canada", "toronto"]:
                    detected_country = "Canada"
                elif cnt in ["usa", "us"]:
                    detected_country = "USA"
                break

        visa_sponsorship = any(w in text_lower for w in ["visa", "sponsorship", "relocation", "abroad", "europe"])

        query_tokens = [seniority] if seniority in ["Senior", "Lead"] else []
        if found_tech:
            query_tokens.extend(found_tech[:2])
        query_tokens.append(role)
        clean_query = " ".join(query_tokens)

        tech_summary = ", ".join(found_tech[:4]) if found_tech else "core technologies"
        return {
            "primary_role": role,
            "technologies": found_tech,
            "seniority": seniority,
            "clean_query": clean_query,
            "detected_location": detected_loc,
            "detected_country": detected_country,
            "is_remote": is_remote,
            "visa_sponsorship": visa_sponsorship,
            "summary_intent": f"Targeting {seniority} {role} roles working with {tech_summary}."
        }

    async def evaluate_resume_fit_for_job(
        self,
        resume_text: str,
        target_role: str,
        job_description: Optional[str] = None,
        company: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate how well a candidate's resume matches a specific target job opening."""
        if not resume_text or len(resume_text.strip()) < 50:
            return {
                "fit_score": 40,
                "verdict": "⚠️ Resume Content Missing or Incomplete",
                "target_role": target_role,
                "target_company": company or "N/A",
                "matching_skills": [],
                "missing_skills_and_gaps": ["Unable to read complete resume. Re-upload your resume PDF."],
                "seniority_alignment": "Unknown",
                "bullet_tailoring_tips": [],
                "actionable_next_steps": ["Upload a detailed PDF resume with `/profile resume`."]
            }

        job_desc = job_description or f"Opening for {target_role} at {company or 'Target Company'}."

        prompt = (
            "You are a Senior Technical Hiring Manager and Applicant Tracking System (ATS) Expert. "
            "Evaluate how well the candidate's resume fits the target job opening.\n\n"
            f"Target Role: {target_role}\n"
            f"Target Company: {company or 'Not specified'}\n"
            f"Job Description & Requirements:\n{job_desc[:3000]}\n\n"
            f"Candidate Resume Content:\n{resume_text[:5000]}\n\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "fit_score": <int between 0 and 100>,\n'
            '  "verdict": "<e.g. 🔥 Strong Fit (Ready to Apply) / ⚠️ Moderate Fit (Tailoring Recommended) / ❌ Significant Skill Gaps>",\n'
            '  "target_role": "' + target_role + '",\n'
            '  "target_company": "' + (company or "N/A") + '",\n'
            '  "matching_skills": ["<matching tech/skill 1>", "<matching skill 2>", "<matching skill 3>"],\n'
            '  "missing_skills_and_gaps": ["<critical required skill missing on resume 1>", "<missing skill 2>"],\n'
            '  "seniority_alignment": "<1-2 sentences on whether candidate experience matches the role level>",\n'
            '  "bullet_tailoring_tips": [\n'
            '    {\n'
            '      "section": "<e.g. Experience / Projects>",\n'
            '      "advice": "<specific advice on what to highlight for this job>",\n'
            '      "example_bullet": "<recommended Google XYZ format bullet point tailoring to this role>"\n'
            '    }\n'
            '  ],\n'
            '  "actionable_next_steps": ["<step 1 before applying>", "<step 2>"]\n'
            "}"
        )
        raw_response = await self.call_chat_completion(prompt, model=model)
        if raw_response:
            parsed = self._clean_and_parse_json(raw_response)
            if isinstance(parsed, dict) and "fit_score" in parsed:
                return parsed

        # Heuristic resume job fit evaluator
        return self._heuristic_resume_job_fit(resume_text, target_role, job_desc, company)

    def _heuristic_resume_job_fit(
        self,
        resume_text: str,
        target_role: str,
        job_description: str,
        company: Optional[str]
    ) -> Dict[str, Any]:
        """Rule-based resume to job fit calculation."""
        res_lower = resume_text.lower()
        job_lower = (job_description + " " + target_role).lower()

        popular_skills = [
            "python", "java", "go", "golang", "javascript", "typescript", "react", "next.js",
            "node.js", "docker", "kubernetes", "aws", "gcp", "azure", "kafka", "redis",
            "sql", "postgresql", "mongodb", "fastapi", "spring boot", "microservices", "ci/cd",
            "graphql", "rest api", "system design", "distributed systems", "git"
        ]

        skills_in_job = [s for s in popular_skills if s in job_lower]
        if not skills_in_job:
            skills_in_job = ["python", "sql", "microservices", "docker", "aws"]

        matching = [s.title() for s in skills_in_job if s in res_lower]
        missing = [s.title() for s in skills_in_job if s not in res_lower]

        # Calculate score
        if skills_in_job:
            match_ratio = len(matching) / len(skills_in_job)
            fit_score = int(45 + (match_ratio * 45))
        else:
            fit_score = 70

        if target_role.lower() in res_lower:
            fit_score += 10
        fit_score = max(30, min(95, fit_score))

        if fit_score >= 80:
            verdict = "🔥 Strong Fit — Your profile aligns well with this opening!"
        elif fit_score >= 60:
            verdict = "⚠️ Moderate Match — Relevant foundation, but some required tech is missing."
        else:
            verdict = "❌ Skill Gaps Detected — Major requirements are not reflected on your resume."

        tailoring_tips = [
            {
                "section": "Technical Skills & Summary",
                "advice": f"Ensure {', '.join(matching[:3]) if matching else 'core frameworks'} are positioned prominently at the top of your resume.",
                "example_bullet": f"Architected scalable backend systems using {matching[0] if matching else 'modern stack'}, ensuring high availability and 99.9% uptime."
            }
        ]
        if missing:
            tailoring_tips.append({
                "section": "Work Experience / Key Projects",
                "advice": f"Add project or hobby work demonstrating experience with {missing[0]}.",
                "example_bullet": f"Integrated {missing[0]} pipelines to automate workflow processing and reduce cycle times by 30%."
            })

        return {
            "fit_score": fit_score,
            "verdict": verdict,
            "target_role": target_role,
            "target_company": company or "N/A",
            "matching_skills": matching or ["General Software Engineering", "Problem Solving"],
            "missing_skills_and_gaps": missing or ["No major keyword gaps detected!"],
            "seniority_alignment": "Experience level is in range; tailor bullet points to match the target responsibility scope.",
            "bullet_tailoring_tips": tailoring_tips,
            "actionable_next_steps": [
                f"Incorporate missing keywords ({', '.join(missing[:3])}) if you have relevant experience.",
                "Quantify accomplishments with business outcomes and metrics before submitting.",
                "Run `/jobs apply` once your resume reflects these key competencies."
            ]
        }

    async def discover_company_career_portal(
        self,
        company_name: str,
        target_role: str = "Software Engineer",
        location: str = "India",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use OpenRouter AI to dynamically discover exact official career portal, ATS link, and hiring info for any company."""
        clean_comp = company_name.strip()
        if not clean_comp:
            return {
                "name": "Tech Company",
                "portal_name": "Careers Portal",
                "home_url": "https://careers.google.com",
                "apply_url": "https://www.google.com/about/careers",
                "tech_stack": ["Python", "Java", "Cloud"],
                "ats_type": "DIRECT_CAREER",
                "hiring_locations": [location],
                "description": "Explore engineering opportunities."
            }

        prompt = (
            f"You are an expert tech recruiter and talent intelligence AI. "
            f"Provide the exact official career portal and hiring intelligence for the company: '{clean_comp}'.\n"
            f"Candidate target role: '{target_role}', location: '{location}'.\n\n"
            f"Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "name": "<Official canonical company name, e.g. Google, Swiggy, Uber>",\n'
            '  "portal_name": "<Display name of their career portal, e.g. Google Careers, Swiggy Careers>",\n'
            '  "home_url": "<Official root careers page URL, e.g. https://careers.google.com or https://careers.swiggy.com>",\n'
            '  "apply_url": "<Exact job search URL for target role, e.g. https://www.google.com/about/careers/applications/jobs/results/?q=Software+Engineer or Workday/Greenhouse/Lever/Ashby URL>",\n'
            '  "tech_stack": ["<key tech 1>", "<key tech 2>", "<key tech 3>", "<key tech 4>"],\n'
            '  "ats_type": "<DIRECT_CAREER or ATS_PORTAL or WORKDAY or GREENHOUSE>",\n'
            '  "hiring_locations": ["<top location 1>", "<top location 2>", "<top location 3>"],\n'
            '  "interview_rounds": ["<e.g. Online Assessment>", "<DSA / Problem Solving>", "<System Design / LLD>", "<Hiring Manager / Values>"],\n'
            '  "description": "<2-sentence description of the company engineering team, products, and hiring culture>"\n'
            "}"
        )

        raw_response = await self.call_chat_completion(prompt, model=model)
        if raw_response:
            parsed = self._clean_and_parse_json(raw_response)
            if isinstance(parsed, dict) and "apply_url" in parsed:
                return parsed

        # Static / Heuristic fallback if OpenRouter API unavailable or fails
        from services.company_directory import get_company_career_url
        return get_company_career_url(clean_comp, target_role, location)

    async def resolve_tech_stack_or_query(
        self,
        query: str,
        location: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze search query using OpenRouter AI to determine if it is a tech stack,
        specific job title, or candidate prompt.
        Expands tech stacks into all matching industry role titles in the target location.
        """
        clean_q = query.strip()
        loc_str = location.strip() if location else "India"

        prompt = (
            f"You are a Senior Technical Recruiter and Job Search Expert. "
            f"Analyze this query: '{clean_q}' in location: '{loc_str}'.\n"
            "Determine if this is a tech stack/technology (e.g. 'Spring Boot', 'React, Node.js', 'Python, FastAPI', 'Golang, Kubernetes'), "
            "a specific job title (e.g. 'Backend Engineer', 'Product Manager'), or natural language search.\n"
            "If it is a tech stack, identify all industry job roles that use this tech stack in that location.\n\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "is_tech_stack": <true/false>,\n'
            '  "detected_tech_stack": ["<tech 1>", "<tech 2>"],\n'
            '  "primary_roles": ["<Role 1>", "<Role 2>", "<Role 3>"],\n'
            '  "refined_keywords": "<optimal search query for LinkedIn & Naukri>",\n'
            '  "summary_intent": "<1-line summary, e.g. Targeting roles using Spring Boot & Microservices in Pune>"\n'
            "}"
        )

        raw_response = await self.call_chat_completion(prompt, model=model)
        if raw_response:
            parsed = self._clean_and_parse_json(raw_response)
            if isinstance(parsed, dict) and "primary_roles" in parsed:
                return parsed

        # Heuristic fallback for tech stack resolution
        q_lower = clean_q.lower()
        tech_roles_map = {
            "spring boot": ["Java Developer", "Spring Boot Developer", "Backend Software Engineer"],
            "spring": ["Java Developer", "Spring Boot Developer", "Backend Engineer"],
            "java": ["Java Developer", "Backend Software Engineer", "Full Stack Java Developer"],
            "react": ["React Developer", "Frontend Engineer", "Full Stack Developer (React)"],
            "angular": ["Angular Developer", "Frontend Engineer", "UI Developer"],
            "vue": ["Vue.js Developer", "Frontend Engineer", "UI Developer"],
            "python": ["Python Developer", "Backend Engineer", "Data Engineer"],
            "django": ["Python Django Developer", "Backend Engineer", "Full Stack Developer"],
            "fastapi": ["Python FastAPI Backend Developer", "API Engineer", "Backend Software Engineer"],
            "golang": ["Golang Developer", "Backend Software Engineer (Go)", "Distributed Systems Engineer"],
            "go": ["Golang Developer", "Backend Software Engineer", "Cloud Engineer"],
            "node": ["Node.js Developer", "Backend Developer", "Full Stack Engineer (MERN)"],
            "nodejs": ["Node.js Developer", "Backend Developer", "Full Stack Engineer"],
            "kubernetes": ["DevOps Engineer", "Site Reliability Engineer (SRE)", "Cloud Platform Engineer"],
            "docker": ["DevOps Engineer", "Cloud Infrastructure Engineer", "Backend Developer"],
            "aws": ["AWS Cloud Engineer", "DevOps Engineer", "Cloud Solutions Architect"],
            "flutter": ["Flutter Developer", "Mobile App Engineer", "Cross-Platform Mobile Developer"],
            "swift": ["iOS Developer", "Mobile Engineer (iOS)", "Swift Developer"],
            "kotlin": ["Android Developer", "Mobile Software Engineer", "Kotlin Backend Engineer"],
            "kafka": ["Data Streaming Engineer", "Backend Software Engineer", "Distributed Systems Engineer"],
            "data science": ["Data Scientist", "Machine Learning Engineer", "AI Specialist"],
            "machine learning": ["Machine Learning Engineer", "AI/ML Developer", "Data Scientist"]
        }

        matched_roles = []
        is_tech = False
        detected_tech = []

        for key, roles in tech_roles_map.items():
            if key in q_lower:
                is_tech = True
                detected_tech.append(key.title())
                for r in roles:
                    if r not in matched_roles:
                        matched_roles.append(r)

        if is_tech and matched_roles:
            return {
                "is_tech_stack": True,
                "detected_tech_stack": detected_tech,
                "primary_roles": matched_roles[:4],
                "refined_keywords": f"{detected_tech[0]} Developer",
                "summary_intent": f"Targeting roles using {', '.join(detected_tech)} in {loc_str}."
            }

        return {
            "is_tech_stack": False,
            "detected_tech_stack": [],
            "primary_roles": [clean_q.title()],
            "refined_keywords": clean_q,
            "summary_intent": f"Searching for {clean_q.title()} roles in {loc_str}."
        }

# Aliases and singletons for ease of access
openrouter_service = OpenRouterAIService()
GeminiResumeService = OpenRouterAIService
gemini_service = openrouter_service

