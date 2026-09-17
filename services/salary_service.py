import urllib.parse
from typing import List, Dict, Any, Optional

# Mapping of common roles to similar/adjacent roles in the industry
SIMILAR_ROLES_MAP: Dict[str, List[str]] = {
    "software engineer": [
        "Backend Engineer",
        "Frontend Engineer",
        "Full Stack Engineer",
        "DevOps Engineer",
        "Tech Lead"
    ],
    "sde": [
        "Software Engineer",
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Senior SDE"
    ],
    "backend": [
        "Software Engineer",
        "Full Stack Engineer",
        "System Architect",
        "DevOps Engineer",
        "Data Engineer"
    ],
    "frontend": [
        "Software Engineer",
        "UI/UX Developer",
        "Full Stack Engineer",
        "React Developer",
        "Web Developer"
    ],
    "full stack": [
        "Software Engineer",
        "Backend Engineer",
        "Frontend Engineer",
        "Technical Lead",
        "Solutions Architect"
    ],
    "data scientist": [
        "Machine Learning Engineer",
        "Data Analyst",
        "Data Engineer",
        "AI Researcher",
        "BI Analyst"
    ],
    "data analyst": [
        "Data Scientist",
        "Business Analyst",
        "Data Engineer",
        "BI Developer",
        "Analytics Manager"
    ],
    "data engineer": [
        "Big Data Engineer",
        "Backend Engineer",
        "Database Administrator",
        "Data Architect",
        "Data Scientist"
    ],
    "machine learning": [
        "Data Scientist",
        "AI Engineer",
        "Deep Learning Specialist",
        "Computer Vision Engineer",
        "MLOps Engineer"
    ],
    "product manager": [
        "Associate Product Manager",
        "Senior Product Manager",
        "Technical Product Manager",
        "Product Owner",
        "Group Product Manager"
    ],
    "devops": [
        "Site Reliability Engineer (SRE)",
        "Cloud Engineer",
        "Platform Engineer",
        "Infrastructure Engineer",
        "Security Engineer"
    ],
    "qa": [
        "SDET",
        "Automation Test Engineer",
        "Software Engineer",
        "Quality Lead"
    ],
    "sdet": [
        "QA Automation Engineer",
        "Software Engineer",
        "Backend Engineer",
        "Test Lead"
    ],
    "engineering manager": [
        "Tech Lead",
        "Director of Engineering",
        "Software Development Manager",
        "VP of Engineering"
    ]
}

class SalaryService:
    """Service to generate authentic salary benchmark links and similar role comparisons across AmbitionBox & Glassdoor."""

    def find_similar_roles(self, role: str) -> List[str]:
        """Find adjacent/similar roles based on the target role title."""
        role_lower = role.lower().strip()
        
        # Check direct key match or substring match
        for key, similar_list in SIMILAR_ROLES_MAP.items():
            if key in role_lower:
                return similar_list

        # Generic tech fallback if contains 'developer' or 'engineer'
        if "engineer" in role_lower or "developer" in role_lower:
            return ["Software Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Developer"]
        elif "manager" in role_lower:
            return ["Product Manager", "Project Manager", "Engineering Manager"]
        elif "analyst" in role_lower:
            return ["Data Analyst", "Business Analyst", "Financial Analyst"]

        return ["Software Engineer", "Senior Associate", "Lead Consultant"]

    def get_salary_benchmarks(
        self,
        role: str,
        company: Optional[str] = None,
        location: Optional[str] = "India"
    ) -> Dict[str, Any]:
        """Generate comprehensive AmbitionBox, Glassdoor, and Levels.fyi links for role & similar roles."""
        clean_role = role.split("—")[-1].strip() if "—" in role else role.strip()
        comp_clean = company.strip() if company and "Live" not in company and "Portal" not in company else None
        
        similar_roles = self.find_similar_roles(clean_role)

        # AmbitionBox links
        if comp_clean:
            ambitionbox_company_role = f"https://www.ambitionbox.com/salaries?company={urllib.parse.quote(comp_clean)}&designation={urllib.parse.quote(clean_role)}"
            ambitionbox_company_all = f"https://www.ambitionbox.com/salaries?company={urllib.parse.quote(comp_clean)}"
            ambitionbox_reviews = f"https://www.ambitionbox.com/reviews?company={urllib.parse.quote(comp_clean)}"
        else:
            ambitionbox_company_role = None
            ambitionbox_company_all = None
            ambitionbox_reviews = None

        ambitionbox_market_role = f"https://www.ambitionbox.com/salaries?designation={urllib.parse.quote(clean_role)}"
        
        ambitionbox_similar = [
            {
                "role": sim,
                "url": f"https://www.ambitionbox.com/salaries?designation={urllib.parse.quote(sim)}"
            }
            for sim in similar_roles[:4]
        ]

        # Glassdoor links
        if comp_clean:
            glassdoor_company_role = f"https://www.glassdoor.co.in/Search/results.htm?keyword={urllib.parse.quote(f'{comp_clean} {clean_role} salaries')}"
            glassdoor_reviews = f"https://www.glassdoor.co.in/Search/results.htm?keyword={urllib.parse.quote(f'{comp_clean} reviews')}"
        else:
            glassdoor_company_role = None
            glassdoor_reviews = None

        glassdoor_market_role = f"https://www.glassdoor.co.in/Search/results.htm?keyword={urllib.parse.quote(f'{clean_role} salaries')}"
        
        glassdoor_similar = [
            {
                "role": sim,
                "url": f"https://www.glassdoor.co.in/Search/results.htm?keyword={urllib.parse.quote(f'{sim} salaries')}"
            }
            for sim in similar_roles[:4]
        ]

        # Levels.fyi link
        levels_query = f"{comp_clean} {clean_role}" if comp_clean else clean_role
        levels_url = f"https://www.levels.fyi/search?q={urllib.parse.quote(levels_query)}"

        return {
            "role": clean_role,
            "company": comp_clean,
            "location": location or "India",
            "ambitionbox": {
                "company_role_url": ambitionbox_company_role,
                "company_all_url": ambitionbox_company_all,
                "company_reviews_url": ambitionbox_reviews,
                "market_role_url": ambitionbox_market_role,
                "similar_roles": ambitionbox_similar
            },
            "glassdoor": {
                "company_role_url": glassdoor_company_role,
                "company_reviews_url": glassdoor_reviews,
                "market_role_url": glassdoor_market_role,
                "similar_roles": glassdoor_similar
            },
            "levels_fyi_url": levels_url,
            "similar_role_names": similar_roles
        }

    def compare_salaries_across_companies(
        self,
        role: str,
        companies: List[str]
    ) -> Dict[str, Any]:
        """Generate side-by-side AmbitionBox & Glassdoor benchmark links across multiple dream companies."""
        clean_role = role.split("—")[-1].strip() if "—" in role else role.strip()
        
        company_data = []
        for comp in companies:
            c = comp.strip()
            if not c:
                continue
            ab_url = f"https://www.ambitionbox.com/salaries?company={urllib.parse.quote(c)}&designation={urllib.parse.quote(clean_role)}"
            gd_url = f"https://www.glassdoor.co.in/Search/results.htm?keyword={urllib.parse.quote(f'{c} {clean_role} salaries')}"
            levels_url = f"https://www.levels.fyi/search?q={urllib.parse.quote(f'{c} {clean_role}')}"
            company_data.append({
                "company": c,
                "ambitionbox_url": ab_url,
                "glassdoor_url": gd_url,
                "levels_url": levels_url
            })

        return {
            "role": clean_role,
            "companies": company_data,
            "market_ambitionbox": f"https://www.ambitionbox.com/salaries?designation={urllib.parse.quote(clean_role)}",
            "market_glassdoor": f"https://www.glassdoor.co.in/Search/results.htm?keyword={urllib.parse.quote(f'{clean_role} salaries')}"
        }

salary_service = SalaryService()
