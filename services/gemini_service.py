import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class GeminiResumeService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI client: {e}")

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

    async def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """Deep critique and improvement audit using Google Gemini AI."""
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

        # If Gemini API Key is available, invoke Gemini AI
        if self._client and self.api_key:
            try:
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

                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                
                raw_text = response.text.strip()
                # Clean markdown codeblocks if wrapped in ```json ... ```
                cleaned = re.sub(r"^```json\s*", "", raw_text)
                cleaned = re.sub(r"```$", "", cleaned).strip()
                parsed = json.loads(cleaned)
                return parsed

            except Exception as e:
                logger.error(f"Error calling Gemini AI API for resume analysis: {e}", exc_info=True)

        # Intelligent heuristic fallback analysis
        return self._heuristic_resume_analysis(resume_text)

    async def extract_resume_profile(self, resume_text: str) -> Dict[str, Any]:
        """Extract candidate skills, target roles, and experience from resume text."""
        if self._client and self.api_key and resume_text:
            try:
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
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                cleaned = re.sub(r"^```json\s*", "", response.text.strip())
                cleaned = re.sub(r"```$", "", cleaned).strip()
                return json.loads(cleaned)
            except Exception as e:
                logger.warning(f"Gemini profile extraction fallback: {e}")

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

gemini_service = GeminiResumeService()
