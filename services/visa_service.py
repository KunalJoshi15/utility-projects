import urllib.parse
from typing import List, Dict, Any, Optional

# Verified global tech employers directory actively offering Visa Sponsorship & Relocation
VISA_SPONSOR_DIRECTORIES: Dict[str, Dict[str, Any]] = {
    "Germany": {
        "flag": "🇩🇪",
        "region": "Germany (Berlin / Munich / Frankfurt / Hamburg)",
        "visa_program": "EU Blue Card (Fast-track Permanent Residency in 21-27 months)",
        "tech_salary_threshold": "€45,300/year (Shortage occupation: Software/IT)",
        "official_register_url": "https://www.make-it-in-germany.com/en/visa-residence/types/eu-blue-card",
        "job_boards": [
            {"name": "Relocate.me Germany", "url": "https://relocate.me/search?query=software&location=Germany"},
            {"name": "Honeypot EU", "url": "https://www.honeypot.io/"},
            {"name": "LinkedIn Germany Visa Sponsor", "url": "https://de.linkedin.com/jobs/search/?keywords=software+engineer+visa+sponsorship&location=Germany"}
        ],
        "top_sponsors": [
            {"name": "Delivery Hero", "career_url": "https://careers.deliveryhero.com/", "notes": "Full relocation & visa assistance (Berlin HQ)"},
            {"name": "Zalando", "career_url": "https://jobs.zalando.com/", "notes": "Active visa sponsorship for engineers & data scientists"},
            {"name": "SAP", "career_url": "https://jobs.sap.com/", "notes": "Global sponsor, Waldorf/Berlin offices"},
            {"name": "N26", "career_url": "https://n26.com/en-de/careers", "notes": "Fintech EU Blue Card sponsor (Berlin)"},
            {"name": "Personio", "career_url": "https://www.personio.com/careers/", "notes": "HR tech unicorn (Munich HQ) with visa support"},
            {"name": "HelloFresh", "career_url": "https://careers.hellofresh.com/", "notes": "International hiring with relocation package"},
            {"name": "Celonis", "career_url": "https://www.celonis.com/careers/", "notes": "Process mining decacorn (Munich)"},
            {"name": "Trade Republic", "career_url": "https://traderepublic.com/en-de/careers", "notes": "Top European neobroker sponsor"}
        ]
    },
    "Netherlands": {
        "flag": "🇳🇱",
        "region": "Netherlands (Amsterdam / Eindhoven / Utrecht / Rotterdam)",
        "visa_program": "Highly Skilled Migrant (HSM) + 30% Tax Ruling Benefit",
        "tech_salary_threshold": "€3,923/month (>30 yrs) or €2,876/month (<30 yrs)",
        "official_register_url": "https://ind.nl/en/public-register-recognised-sponsors",
        "job_boards": [
            {"name": "Relocate.me Netherlands", "url": "https://relocate.me/search?query=software&location=Netherlands"},
            {"name": "LinkedIn Netherlands Visa", "url": "https://nl.linkedin.com/jobs/search/?keywords=software+engineer+visa+sponsorship&location=Netherlands"},
            {"name": "Landing.jobs NL", "url": "https://landing.jobs/jobs?relocation=true&visa=true"}
        ],
        "top_sponsors": [
            {"name": "ASML", "career_url": "https://www.asml.com/en/careers", "notes": "Global semiconductor leader (Eindhoven), huge international hiring"},
            {"name": "Booking.com", "career_url": "https://careers.booking.com/", "notes": "Amsterdam Global HQ, comprehensive relocation & visa"},
            {"name": "Uber Amsterdam", "career_url": "https://www.uber.com/global/en/careers/", "notes": "EMEA Tech Hub (Amsterdam), active visa sponsor"},
            {"name": "Miro", "career_url": "https://miro.com/careers/", "notes": "Co-HQ in Amsterdam with visa & relocation sponsorship"},
            {"name": "Adyen", "career_url": "https://careers.adyen.com/", "notes": "Leading global fintech payment platform"},
            {"name": "Optiver", "career_url": "https://optiver.com/working-at-optiver/", "notes": "Prop trading firm with top tier relocation & pay"},
            {"name": "IMC Trading", "career_url": "https://careers.imc.com/", "notes": "Tech-driven market maker in Amsterdam"},
            {"name": "Elastic", "career_url": "https://www.elastic.co/careers/", "notes": "Search engine company with Dutch roots & remote/visa options"}
        ]
    },
    "UK": {
        "flag": "🇬🇧",
        "region": "United Kingdom (London / Edinburgh / Cambridge / Manchester)",
        "visa_program": "UK Skilled Worker Visa (Licensed Home Office Sponsors)",
        "tech_salary_threshold": "£38,700/year (or going rate for role)",
        "official_register_url": "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
        "job_boards": [
            {"name": "Relocate.me UK", "url": "https://relocate.me/search?query=software&location=United+Kingdom"},
            {"name": "LinkedIn UK Visa", "url": "https://uk.linkedin.com/jobs/search/?keywords=software+engineer+visa+sponsorship&location=United+Kingdom"},
            {"name": "Indeed UK Visa Feed", "url": "https://uk.indeed.com/jobs?q=visa+sponsorship+software+engineer&l=London"}
        ],
        "top_sponsors": [
            {"name": "Revolut", "career_url": "https://www.revolut.com/careers/", "notes": "London HQ, licensed Tier 2 sponsor"},
            {"name": "Bloomberg London", "career_url": "https://www.bloomberg.com/careers/technology/", "notes": "Massive engineering office in London with full sponsorship"},
            {"name": "Google DeepMind", "career_url": "https://deepmind.google/about/careers/", "notes": "Premier AI research lab in London with visa sponsorship"},
            {"name": "Monzo", "career_url": "https://monzo.com/careers/", "notes": "Digital bank in London sponsoring tech roles"},
            {"name": "Wise", "career_url": "https://www.wise.jobs/", "notes": "Global payment network (London/Shoreditch)"},
            {"name": "Deliveroo", "career_url": "https://careers.deliveroo.co.uk/", "notes": "UK food delivery tech platform"},
            {"name": "Palantir UK", "career_url": "https://www.palantir.com/careers/", "notes": "London R&D center with visa sponsorship"},
            {"name": "Meta London", "career_url": "https://www.metacareers.com/", "notes": "Major engineering hub in King's Cross"}
        ]
    },
    "Canada": {
        "flag": "🇨🇦",
        "region": "Canada (Toronto / Vancouver / Montreal / Waterloo)",
        "visa_program": "Global Talent Stream (GTS - 2-week fast-track LMIA work permit)",
        "tech_salary_threshold": "Prevailing wage for NOC tech codes ($85k - $140k CAD)",
        "official_register_url": "https://www.canada.ca/en/employment-social-development/services/foreign-workers/global-talent.html",
        "job_boards": [
            {"name": "Relocate.me Canada", "url": "https://relocate.me/search?query=software&location=Canada"},
            {"name": "LinkedIn Canada Visa", "url": "https://ca.linkedin.com/jobs/search/?keywords=software+engineer+visa+sponsorship&location=Canada"},
            {"name": "Indeed Canada", "url": "https://ca.indeed.com/jobs?q=visa+sponsorship+software&l=Toronto"}
        ],
        "top_sponsors": [
            {"name": "Shopify", "career_url": "https://www.shopify.com/careers", "notes": "Canada's top tech company, Digital by Design"},
            {"name": "Amazon Canada", "career_url": "https://www.amazon.jobs/en/locations/vancouver-canada", "notes": "Huge tech hubs in Vancouver & Toronto with LMIA/GTS"},
            {"name": "Google Canada", "career_url": "https://careers.google.com/locations/waterloo-canada/", "notes": "Waterloo & Toronto tech centers"},
            {"name": "Microsoft Vancouver", "career_url": "https://careers.microsoft.com/", "notes": "Vancouver Development Centre (active global transfer & direct hiring)"},
            {"name": "Faire", "career_url": "https://www.faire.com/careers", "notes": "Wholesale marketplace unicorn (Waterloo/Toronto)"},
            {"name": "Wealthsimple", "career_url": "https://www.wealthsimple.com/en-ca/careers", "notes": "Fintech innovator in Toronto"}
        ]
    },
    "USA": {
        "flag": "🇺🇸",
        "region": "USA (San Francisco / Seattle / New York / Austin)",
        "visa_program": "H-1B Cap / Cap-Exempt, L-1 Intracompany Transferee, O-1 Extraordinary Ability",
        "tech_salary_threshold": "Prevailing wage levels ($120k - $250k+ USD)",
        "official_register_url": "https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations",
        "job_boards": [
            {"name": "Levels.fyi H1B Sponsor Database", "url": "https://www.levels.fyi/h1b/"},
            {"name": "LinkedIn US Visa", "url": "https://www.linkedin.com/jobs/search/?keywords=software+engineer+visa+sponsorship&location=United+States"},
            {"name": "MyVisaJobs Top Sponsors", "url": "https://www.myvisajobs.com/reports/h1b/"}
        ],
        "top_sponsors": [
            {"name": "Google", "career_url": "https://careers.google.com/", "notes": "Top US H-1B & L-1 sponsor globally"},
            {"name": "Microsoft", "career_url": "https://careers.microsoft.com/", "notes": "Extensive international relocation & immigration legal support"},
            {"name": "Amazon", "career_url": "https://www.amazon.jobs/", "notes": "Highest volume H-1B & L-1 transfer employer"},
            {"name": "Meta", "career_url": "https://www.metacareers.com/", "notes": "Menlo Park/Seattle with comprehensive immigration support"},
            {"name": "Apple", "career_url": "https://jobs.apple.com/", "notes": "Cupertino HQ with global talent sponsorship"},
            {"name": "NVIDIA", "career_url": "https://www.nvidia.com/en-us/about-nvidia/careers/", "notes": "AI hardware & software leader sponsoring top engineers"},
            {"name": "Salesforce", "career_url": "https://www.salesforce.com/company/careers/", "notes": "Enterprise cloud leader with H1B/L1 sponsorship"}
        ]
    },
    "Singapore": {
        "flag": "🇸🇬",
        "region": "Singapore (CBD / One-North Tech District)",
        "visa_program": "Ministry of Manpower (MOM) Employment Pass (EP) & COMPASS Points System",
        "tech_salary_threshold": "S$5,600/month (tech track benchmarks up to S$10,500 for senior)",
        "official_register_url": "https://www.mom.gov.sg/passes-and-permits/employment-pass",
        "job_boards": [
            {"name": "MyCareersFuture SG", "url": "https://www.mycareersfuture.gov.sg/"},
            {"name": "LinkedIn Singapore Visa", "url": "https://sg.linkedin.com/jobs/search/?keywords=software+engineer+visa+sponsorship&location=Singapore"}
        ],
        "top_sponsors": [
            {"name": "Grab", "career_url": "https://grab.careers/", "notes": "Singapore SuperApp HQ with strong EP track record"},
            {"name": "Sea / Shopee", "career_url": "https://careers.shopee.sg/", "notes": "Tech giant in Singapore with active foreign tech hiring"},
            {"name": "ByteDance / TikTok SG", "career_url": "https://jobs.bytedance.com/", "notes": "Asia-Pacific Global HQ with extensive sponsorship"},
            {"name": "Google Singapore", "career_url": "https://careers.google.com/locations/singapore/", "notes": "APAC headquarters in Pasir Panjang"},
            {"name": "Stripe Singapore", "career_url": "https://stripe.com/jobs", "notes": "APAC engineering hub with full EP support"}
        ]
    },
    "UAE": {
        "flag": "🇦🇪",
        "region": "United Arab Emirates (Dubai Internet City / Abu Dhabi)",
        "visa_program": "0% Personal Income Tax + UAE Green Visa / 10-Year Golden Visa",
        "tech_salary_threshold": "AED 30,000/month for Golden Visa track",
        "official_register_url": "https://u.ae/en/information-and-services/visa-and-emirates-id/residence-visas/golden-visa",
        "job_boards": [
            {"name": "LinkedIn UAE Tech", "url": "https://ae.linkedin.com/jobs/search/?keywords=software+engineer&location=Dubai"},
            {"name": "GulfTalent Dubai Tech", "url": "https://www.gulftalent.com/uae/jobs/software-engineer"}
        ],
        "top_sponsors": [
            {"name": "Careem", "career_url": "https://jobs.careem.com/", "notes": "Dubai internet city tech powerhouse with direct work residency"},
            {"name": "Noon", "career_url": "https://www.noon.com/careers/", "notes": "E-commerce & fintech leader in UAE"},
            {"name": "Talabat", "career_url": "https://www.talabat.com/careers", "notes": "Delivery Hero MENA branch in Dubai"},
            {"name": "Binance UAE", "career_url": "https://www.binance.com/en/careers", "notes": "Global Web3 leader with major Dubai operations"}
        ]
    }
}

class VisaService:
    """Service to track verified visa-sponsoring employers and international relocation job feeds."""

    def get_supported_countries(self) -> List[str]:
        """Return list of countries with verified visa sponsorship tracking."""
        return list(VISA_SPONSOR_DIRECTORIES.keys())

    def get_country_directory(self, country: str) -> Optional[Dict[str, Any]]:
        """Get visa directory data for a specific country."""
        norm_country = country.strip().title()
        if "germany" in norm_country.lower():
            return VISA_SPONSOR_DIRECTORIES["Germany"]
        elif "netherlands" in norm_country.lower() or "holland" in norm_country.lower() or "amsterdam" in norm_country.lower():
            return VISA_SPONSOR_DIRECTORIES["Netherlands"]
        elif "uk" in norm_country.lower() or "united kingdom" in norm_country.lower() or "london" in norm_country.lower():
            return VISA_SPONSOR_DIRECTORIES["UK"]
        elif "canada" in norm_country.lower() or "toronto" in norm_country.lower() or "vancouver" in norm_country.lower():
            return VISA_SPONSOR_DIRECTORIES["Canada"]
        elif "usa" in norm_country.lower() or "united states" in norm_country.lower():
            return VISA_SPONSOR_DIRECTORIES["USA"]
        elif "singapore" in norm_country.lower():
            return VISA_SPONSOR_DIRECTORIES["Singapore"]
        elif "uae" in norm_country.lower() or "dubai" in norm_country.lower():
            return VISA_SPONSOR_DIRECTORIES["UAE"]
        return None

    def search_visa_jobs(
        self,
        role: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate verified visa sponsorship search feeds for candidates seeking relocation."""
        clean_role = role.split("—")[-1].strip() if "—" in role else role.strip()
        target_country = country.strip().title() if country else "Germany"
        
        country_dir = self.get_country_directory(target_country) or VISA_SPONSOR_DIRECTORIES["Germany"]
        country_name = target_country if self.get_country_directory(target_country) else "Germany"

        encoded_role = urllib.parse.quote(clean_role)
        encoded_country = urllib.parse.quote(country_name)
        encoded_query = urllib.parse.quote(f"{clean_role} visa sponsorship")

        # Construct dedicated international visa job links
        relocate_url = f"https://relocate.me/search?query={encoded_role}&location={encoded_country}"
        linkedin_visa_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={encoded_country}&f_TPR=r604800"
        landing_jobs_url = f"https://landing.jobs/jobs?q={encoded_role}&relocation=true&visa=true"
        indeed_visa_url = f"https://www.indeed.com/jobs?q={encoded_query}&l={encoded_country}"
        google_jobs_visa_url = f"https://www.google.com/search?q={encoded_role}+visa+sponsorship+jobs+in+{encoded_country}&ibp=htl;jobs"
        levels_h1b_url = f"https://www.levels.fyi/h1b/?search={encoded_role}"

        return {
            "role": clean_role,
            "country": country_name,
            "country_info": country_dir,
            "feeds": {
                "relocate_me": relocate_url,
                "linkedin_visa": linkedin_visa_url,
                "landing_jobs": landing_jobs_url,
                "indeed_visa": indeed_visa_url,
                "google_jobs_visa": google_jobs_visa_url,
                "levels_h1b": levels_h1b_url
            },
            "top_sponsors": country_dir.get("top_sponsors", [])[:6]
        }

    def check_company_visa_intel(self, company_name: str) -> Dict[str, Any]:
        """Check known visa sponsorship status and provide official registry lookup links for a company."""
        comp_clean = company_name.strip()
        comp_lower = comp_clean.lower()
        
        # Check against our verified sponsor directories
        found_matches = []
        for country, data in VISA_SPONSOR_DIRECTORIES.items():
            for sponsor in data["top_sponsors"]:
                if sponsor["name"].lower() in comp_lower or comp_lower in sponsor["name"].lower():
                    found_matches.append({
                        "country": country,
                        "flag": data["flag"],
                        "visa_program": data["visa_program"],
                        "notes": sponsor["notes"],
                        "career_url": sponsor["career_url"],
                        "official_register_url": data["official_register_url"]
                    })

        encoded_comp = urllib.parse.quote(comp_clean)
        uk_register_search = f"https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
        levels_fyi_sponsor = f"https://www.levels.fyi/h1b/?search={encoded_comp}"
        myvisajobs_sponsor = f"https://www.myvisajobs.com/Search_Visa_Sponsor.aspx?QS={encoded_comp}"
        linkedin_company_jobs = f"https://www.linkedin.com/jobs/search/?keywords={encoded_comp}+visa+sponsorship"

        return {
            "company": comp_clean,
            "is_verified_in_directory": len(found_matches) > 0,
            "verified_sponsorship_tracks": found_matches,
            "registry_links": {
                "levels_fyi": levels_fyi_sponsor,
                "myvisajobs": myvisajobs_sponsor,
                "uk_home_office": uk_register_search,
                "linkedin_visa_jobs": linkedin_company_jobs
            }
        }

visa_service = VisaService()
