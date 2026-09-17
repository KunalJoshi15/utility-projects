import urllib.parse
from typing import Dict, Any, Optional

COMPANY_CAREER_PORTALS: Dict[str, Dict[str, Any]] = {
    # Big Tech & Global Leaders
    "google": {
        "name": "Google",
        "portal_name": "Google Careers",
        "home_url": "https://careers.google.com/",
        "search_url_template": "https://www.google.com/about/careers/applications/jobs/results/?q={query}",
        "logo_url": "https://www.google.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Official career portal for software engineering, product, AI, and systems roles at Google."
    },
    "amazon": {
        "name": "Amazon",
        "portal_name": "Amazon.jobs",
        "home_url": "https://www.amazon.jobs/",
        "search_url_template": "https://www.amazon.jobs/en/search?base_query={query}&loc_query={location}",
        "logo_url": "https://www.amazon.jobs/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Official openings across AWS, Retail, Prime, and engineering hubs on Amazon.jobs."
    },
    "microsoft": {
        "name": "Microsoft",
        "portal_name": "Microsoft Careers",
        "home_url": "https://careers.microsoft.com/",
        "search_url_template": "https://careers.microsoft.com/v2/global/en/home.html?q={query}",
        "logo_url": "https://careers.microsoft.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Global engineering, cloud (Azure), AI, and developer platform positions at Microsoft."
    },
    "meta": {
        "name": "Meta",
        "portal_name": "Meta Careers",
        "home_url": "https://www.metacareers.com/",
        "search_url_template": "https://www.metacareers.com/jobs/?q={query}",
        "logo_url": "https://www.metacareers.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Openings in infrastructure, AI/ML, PyTorch, Instagram, WhatsApp, and VR at Meta Careers."
    },
    "apple": {
        "name": "Apple",
        "portal_name": "Apple Jobs",
        "home_url": "https://jobs.apple.com/",
        "search_url_template": "https://jobs.apple.com/en-us/search?search={query}&location={location}",
        "logo_url": "https://jobs.apple.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Hardware, software, cloud services, and AI/ML engineering positions at Apple."
    },
    "netflix": {
        "name": "Netflix",
        "portal_name": "Netflix Jobs",
        "home_url": "https://jobs.netflix.com/",
        "search_url_template": "https://jobs.netflix.com/search?q={query}",
        "logo_url": "https://jobs.netflix.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Distributed systems, streaming infrastructure, recommendations, and platform engineering at Netflix."
    },
    "uber": {
        "name": "Uber",
        "portal_name": "Uber Careers",
        "home_url": "https://www.uber.com/global/en/careers/",
        "search_url_template": "https://www.uber.com/global/en/careers/list/?query={query}",
        "logo_url": "https://www.uber.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Real-time dispatch, maps, marketplaces, mobility, and delivery tech vacancies at Uber."
    },
    "atlassian": {
        "name": "Atlassian",
        "portal_name": "Atlassian Careers",
        "home_url": "https://www.atlassian.com/company/careers",
        "search_url_template": "https://www.atlassian.com/company/careers/all-jobs?search={query}",
        "logo_url": "https://www.atlassian.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Remote-first engineering vacancies across Jira, Confluence, and cloud platform services."
    },
    "adobe": {
        "name": "Adobe",
        "portal_name": "Adobe Careers",
        "home_url": "https://careers.adobe.com/",
        "search_url_template": "https://careers.adobe.com/us/en/search-results?keywords={query}",
        "logo_url": "https://careers.adobe.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Creative Cloud, Document Cloud, Experience Platform, and Firefly AI engineering at Adobe."
    },
    "salesforce": {
        "name": "Salesforce",
        "portal_name": "Salesforce Careers",
        "home_url": "https://careers.salesforce.com/",
        "search_url_template": "https://careers.salesforce.com/en/jobs/?search={query}",
        "logo_url": "https://careers.salesforce.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "CRM, cloud architecture, Einstein AI, and enterprise data platform opportunities at Salesforce."
    },
    "nvidia": {
        "name": "NVIDIA",
        "portal_name": "NVIDIA Careers",
        "home_url": "https://www.nvidia.com/en-us/about-nvidia/careers/",
        "search_url_template": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite?q={query}",
        "logo_url": "https://www.nvidia.com/favicon.ico",
        "ats_type": "ATS_PORTAL",
        "description": "CUDA, GPU compute, deep learning software, compilers, and hardware systems roles at NVIDIA."
    },
    "stripe": {
        "name": "Stripe",
        "portal_name": "Stripe Jobs",
        "home_url": "https://stripe.com/jobs",
        "search_url_template": "https://stripe.com/jobs/search?query={query}",
        "logo_url": "https://stripe.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Financial infrastructure, distributed ledger, payments APIs, and risk systems at Stripe."
    },
    "oracle": {
        "name": "Oracle",
        "portal_name": "Oracle Careers",
        "home_url": "https://careers.oracle.com/",
        "search_url_template": "https://careers.oracle.com/jobs/search?keyword={query}",
        "logo_url": "https://careers.oracle.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Oracle Cloud Infrastructure (OCI), autonomous databases, and enterprise cloud applications."
    },
    "cisco": {
        "name": "Cisco",
        "portal_name": "Cisco Jobs",
        "home_url": "https://jobs.cisco.com/",
        "search_url_template": "https://jobs.cisco.com/jobs/SearchJobs/?keyword={query}",
        "logo_url": "https://jobs.cisco.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Networking, cybersecurity (Splunk, Talos), cloud observability, and systems software at Cisco."
    },
    "spotify": {
        "name": "Spotify",
        "portal_name": "Life at Spotify",
        "home_url": "https://www.lifeatspotify.com/",
        "search_url_template": "https://www.lifeatspotify.com/jobs?q={query}",
        "logo_url": "https://www.lifeatspotify.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Audio streaming, recommendation engines, creator tools, and client platforms at Spotify."
    },
    "airbnb": {
        "name": "Airbnb",
        "portal_name": "Airbnb Careers",
        "home_url": "https://careers.airbnb.com/",
        "search_url_template": "https://careers.airbnb.com/positions/",
        "logo_url": "https://careers.airbnb.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Global travel marketplace, booking infrastructure, and mobile engineering at Airbnb."
    },
    "databricks": {
        "name": "Databricks",
        "portal_name": "Databricks Careers",
        "home_url": "https://www.databricks.com/company/careers",
        "search_url_template": "https://www.databricks.com/company/careers/open-positions?title={query}",
        "logo_url": "https://www.databricks.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Apache Spark, Delta Lake, Lakehouse architecture, and generative AI systems at Databricks."
    },
    "snowflake": {
        "name": "Snowflake",
        "portal_name": "Snowflake Careers",
        "home_url": "https://careers.snowflake.com/",
        "search_url_template": "https://careers.snowflake.com/us/en/search-results?keywords={query}",
        "logo_url": "https://careers.snowflake.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Data cloud warehousing, distributed query engines, and data applications at Snowflake."
    },
    "servicenow": {
        "name": "ServiceNow",
        "portal_name": "ServiceNow Careers",
        "home_url": "https://careers.servicenow.com/",
        "search_url_template": "https://careers.servicenow.com/careers/jobs?keywords={query}",
        "logo_url": "https://careers.servicenow.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Enterprise workflow automation, cloud platform infrastructure, and IT service intelligence."
    },
    "paypal": {
        "name": "PayPal",
        "portal_name": "PayPal Careers",
        "home_url": "https://careers.pypl.com/",
        "search_url_template": "https://careers.pypl.com/job-search-results/?keyword={query}",
        "logo_url": "https://careers.pypl.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Digital payments, merchant systems, fraud prevention, and Venmo/Braintree engineering."
    },
    "intuit": {
        "name": "Intuit",
        "portal_name": "Intuit Careers",
        "home_url": "https://jobs.intuit.com/",
        "search_url_template": "https://jobs.intuit.com/search-jobs/{query}",
        "logo_url": "https://jobs.intuit.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "TurboTax, QuickBooks, Credit Karma, and financial AI platform roles at Intuit."
    },
    "walmart": {
        "name": "Walmart Global Tech",
        "portal_name": "Walmart Tech Careers",
        "home_url": "https://careers.walmart.com/",
        "search_url_template": "https://careers.walmart.com/results?q={query}",
        "logo_url": "https://careers.walmart.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Retail tech scale, supply chain automation, omnichannel cloud, and e-commerce systems."
    },
    "target": {
        "name": "Target Tech",
        "portal_name": "Target Careers",
        "home_url": "https://corporate.target.com/careers",
        "search_url_template": "https://corporate.target.com/careers/search-jobs?k={query}",
        "logo_url": "https://corporate.target.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Target enterprise technology, store platform software, and data engineering."
    },
    "goldman": {
        "name": "Goldman Sachs",
        "portal_name": "Goldman Sachs Careers",
        "home_url": "https://www.goldmansachs.com/careers/",
        "search_url_template": "https://www.goldmansachs.com/careers/our-firm/engineering/",
        "logo_url": "https://www.goldmansachs.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Quantitative engineering, algorithmic trading, asset management, and fintech platform systems."
    },
    "morgan stanley": {
        "name": "Morgan Stanley",
        "portal_name": "Morgan Stanley Careers",
        "home_url": "https://www.morganstanley.com/about-us/careers",
        "search_url_template": "https://www.morganstanley.com/about-us/careers",
        "logo_url": "https://www.morganstanley.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "High-frequency trading platforms, wealth management tech, and institutional cybersecurity."
    },
    "jpmorgan": {
        "name": "JPMorgan Chase",
        "portal_name": "JPMorgan Chase Careers",
        "home_url": "https://careers.jpmorgan.com/",
        "search_url_template": "https://careers.jpmorgan.com/global/en/home",
        "logo_url": "https://careers.jpmorgan.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Global banking platform infrastructure, payments modernization, and cloud engineering."
    },

    # Indian Tech Unicorns & Product Companies
    "swiggy": {
        "name": "Swiggy",
        "portal_name": "Swiggy Careers",
        "home_url": "https://careers.swiggy.com/",
        "search_url_template": "https://careers.swiggy.com/",
        "logo_url": "https://www.swiggy.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Official engineering, hyper-local logistics, Instamart, and consumer app roles on Swiggy Careers."
    },
    "flipkart": {
        "name": "Flipkart",
        "portal_name": "Flipkart Careers",
        "home_url": "https://www.flipkartcareers.com/",
        "search_url_template": "https://www.flipkartcareers.com/#!/searchjobs",
        "logo_url": "https://www.flipkartcareers.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "India's e-commerce leader — supply chain, high-throughput backend, search & ads platform engineering."
    },
    "zomato": {
        "name": "Zomato",
        "portal_name": "Zomato Careers",
        "home_url": "https://www.zomato.com/careers",
        "search_url_template": "https://www.zomato.com/careers",
        "logo_url": "https://www.zomato.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Food delivery, dining discovery, Blinkit quick commerce, and Hyperpure supply tech at Zomato."
    },
    "blinkit": {
        "name": "Blinkit",
        "portal_name": "Blinkit Careers",
        "home_url": "https://blinkit.com/careers",
        "search_url_template": "https://blinkit.com/careers",
        "logo_url": "https://blinkit.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Quick commerce 10-minute dark store dispatch, warehouse automation, and backend engineering."
    },
    "zepto": {
        "name": "Zepto",
        "portal_name": "Zepto Careers",
        "home_url": "https://www.zeptonow.com/careers",
        "search_url_template": "https://www.zeptonow.com/careers",
        "logo_url": "https://www.zeptonow.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Fast-growing quick commerce unicorn building micro-fulfillment, routing, and mobile applications."
    },
    "phonepe": {
        "name": "PhonePe",
        "portal_name": "PhonePe Careers",
        "home_url": "https://www.phonepe.com/careers/",
        "search_url_template": "https://www.phonepe.com/careers/",
        "logo_url": "https://www.phonepe.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "India's leading UPI payments app, Indus Appstore, lending, and merchant infrastructure."
    },
    "razorpay": {
        "name": "Razorpay",
        "portal_name": "Razorpay Jobs",
        "home_url": "https://razorpay.com/jobs/",
        "search_url_template": "https://razorpay.com/jobs/",
        "logo_url": "https://razorpay.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Payments gateway, neo-banking (RazorpayX), payroll (Opfin), and cross-border billing systems."
    },
    "cred": {
        "name": "CRED",
        "portal_name": "CRED Careers",
        "home_url": "https://careers.cred.club/",
        "search_url_template": "https://careers.cred.club/",
        "logo_url": "https://careers.cred.club/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "High-trust credit card rewards, UPI payments, peer-to-peer lending, and luxury e-commerce."
    },
    "meesho": {
        "name": "Meesho",
        "portal_name": "Meesho Tech Jobs",
        "home_url": "https://meesho.io/jobs",
        "search_url_template": "https://meesho.io/jobs",
        "logo_url": "https://meesho.io/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Zero-commission social e-commerce, user growth algorithms, and tier 2/3 market tech."
    },
    "groww": {
        "name": "Groww",
        "portal_name": "Groww Careers",
        "home_url": "https://groww.in/careers",
        "search_url_template": "https://groww.in/careers",
        "logo_url": "https://groww.in/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "India's premier investment platform — stocks, mutual funds, derivatives, and wealth tech."
    },
    "zerodha": {
        "name": "Zerodha",
        "portal_name": "Zerodha Tech Careers",
        "home_url": "https://zerodha.com/careers",
        "search_url_template": "https://zerodha.com/careers",
        "logo_url": "https://zerodha.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Kite trading engine, open-source tech, PostgreSQL scale, Go/Python microservices, and Rainmatter fintech."
    },
    "postman": {
        "name": "Postman",
        "portal_name": "Postman Careers",
        "home_url": "https://www.postman.com/company/careers/",
        "search_url_template": "https://www.postman.com/company/careers/",
        "logo_url": "https://www.postman.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Global API platform used by 30M+ developers — desktop client, cloud workspaces, and developer tooling."
    },
    "browserstack": {
        "name": "BrowserStack",
        "portal_name": "BrowserStack Careers",
        "home_url": "https://www.browserstack.com/careers",
        "search_url_template": "https://www.browserstack.com/careers",
        "logo_url": "https://www.browserstack.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Cloud testing infrastructure, real device cloud, automated selenium/playwright pipelines."
    },
    "freshworks": {
        "name": "Freshworks",
        "portal_name": "Freshworks Careers",
        "home_url": "https://www.freshworks.com/company/careers/",
        "search_url_template": "https://www.freshworks.com/company/careers/",
        "logo_url": "https://www.freshworks.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "NASDAQ-listed SaaS pioneer — Freshdesk, Freshservice, CRM, and AI bots for customer support."
    },
    "inmobi": {
        "name": "InMobi / Glance",
        "portal_name": "InMobi Careers",
        "home_url": "https://www.inmobi.com/company/careers",
        "search_url_template": "https://www.inmobi.com/company/careers",
        "logo_url": "https://www.inmobi.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Mobile advertising exchange, lock-screen content platform Glance, and ad-tech AI."
    },
    "urban company": {
        "name": "Urban Company",
        "portal_name": "Urban Company Careers",
        "home_url": "https://careers.urbancompany.com/",
        "search_url_template": "https://careers.urbancompany.com/",
        "logo_url": "https://careers.urbancompany.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Home services marketplace, partner matchmaking algorithms, and service fulfillment systems."
    },
    "lenskart": {
        "name": "Lenskart",
        "portal_name": "Lenskart Careers",
        "home_url": "https://www.lenskart.com/careers",
        "search_url_template": "https://www.lenskart.com/careers",
        "logo_url": "https://www.lenskart.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Omnichannel eyewear retail tech, 3D AR virtual try-on, and automated supply chains."
    },
    "myntra": {
        "name": "Myntra",
        "portal_name": "Myntra Careers",
        "home_url": "https://careers.myntra.com/",
        "search_url_template": "https://careers.myntra.com/",
        "logo_url": "https://careers.myntra.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Fashion e-commerce leader, personalized catalog search, style discovery, and high-scale checkout."
    },
    "nykaa": {
        "name": "Nykaa",
        "portal_name": "Nykaa Careers",
        "home_url": "https://www.nykaa.com/careers",
        "search_url_template": "https://www.nykaa.com/careers",
        "logo_url": "https://www.nykaa.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Beauty & lifestyle e-commerce, content-commerce engine, and logistics tech."
    },
    "delhivery": {
        "name": "Delhivery",
        "portal_name": "Delhivery Careers",
        "home_url": "https://www.delhivery.com/careers/",
        "search_url_template": "https://www.delhivery.com/careers/",
        "logo_url": "https://www.delhivery.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Logistics decacorn — pan-India automated sorting hubs, route optimization, and tracking APIs."
    },
    "ola": {
        "name": "Ola / Ola Electric",
        "portal_name": "Ola Careers",
        "home_url": "https://www.olaelectric.com/careers",
        "search_url_template": "https://www.olaelectric.com/careers",
        "logo_url": "https://www.olaelectric.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "EV vehicle software, battery telematics, MoveOS, and urban ride-hailing networks."
    },
    "paytm": {
        "name": "Paytm",
        "portal_name": "Paytm Careers",
        "home_url": "https://paytm.com/careers/",
        "search_url_template": "https://paytm.com/careers/",
        "logo_url": "https://paytm.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Soundbox IoT, merchant point of sale, QR payments, and digital wealth services."
    },

    # IT Services & Consulting Giants
    "tcs": {
        "name": "Tata Consultancy Services (TCS)",
        "portal_name": "TCS Careers",
        "home_url": "https://www.tcs.com/careers",
        "search_url_template": "https://www.tcs.com/careers",
        "logo_url": "https://www.tcs.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Global enterprise transformation, cloud modernization, and banking/financial services tech."
    },
    "infosys": {
        "name": "Infosys",
        "portal_name": "Infosys Careers",
        "home_url": "https://www.infosys.com/careers/",
        "search_url_template": "https://www.infosys.com/careers/",
        "logo_url": "https://www.infosys.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Cloud services (Cobalt), AI solutions (Topaz), enterprise consulting, and digital engineering."
    },
    "wipro": {
        "name": "Wipro",
        "portal_name": "Wipro Careers",
        "home_url": "https://careers.wipro.com/",
        "search_url_template": "https://careers.wipro.com/",
        "logo_url": "https://careers.wipro.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Cloud infrastructure, cybersecurity, engineering R&D, and AI transformation services."
    },
    "accenture": {
        "name": "Accenture",
        "portal_name": "Accenture Careers",
        "home_url": "https://www.accenture.com/careers",
        "search_url_template": "https://www.accenture.com/in-en/careers/jobsearch?jk={query}",
        "logo_url": "https://www.accenture.com/favicon.ico",
        "ats_type": "DIRECT_CAREER",
        "description": "Strategy, cloud architecture, generative AI implementation, and technology operations."
    }
}


def find_company_match(company_query: str) -> Optional[Dict[str, Any]]:
    """Look up verified company info from alias or name query."""
    if not company_query:
        return None
    
    q = company_query.lower().strip()
    
    # Direct key lookup
    if q in COMPANY_CAREER_PORTALS:
        return COMPANY_CAREER_PORTALS[q]
    
    # Substring / fuzzy alias matching
    for key, data in COMPANY_CAREER_PORTALS.items():
        if key in q or q in key or q in data["name"].lower():
            return data
            
    return None


def get_company_career_url(company_name: str, query: str = "Software Engineer", location: str = "India") -> Dict[str, Any]:
    """
    Get the authentic direct career portal URL and metadata for a company.
    If not in registry, constructs a smart Google Careers direct search link.
    """
    clean_comp = company_name.strip()
    encoded_query = urllib.parse.quote(query.strip())
    encoded_comp = urllib.parse.quote(clean_comp)
    encoded_loc = urllib.parse.quote(location.strip()) if location else "India"

    matched = find_company_match(clean_comp)
    if matched:
        # Build direct search URL
        template = matched.get("search_url_template", matched["home_url"])
        direct_url = template.format(query=encoded_query, location=encoded_loc)
        return {
            "name": matched["name"],
            "portal_name": matched["portal_name"],
            "apply_url": direct_url,
            "home_url": matched["home_url"],
            "logo_url": matched.get("logo_url"),
            "ats_type": matched.get("ats_type", "DIRECT_CAREER"),
            "description": matched.get("description", f"Official job openings and vacancies at {matched['name']}."),
            "is_official_portal": True
        }

    # Dynamic fallback for unindexed companies
    google_career_url = f"https://www.google.com/search?q={encoded_comp}+official+careers+jobs+portal+{encoded_query}&ibp=htl;jobs"
    company_site_url = f"https://www.google.com/search?q=site:careers.{clean_comp.lower().replace(' ', '')}.com+OR+{encoded_comp}+careers+{encoded_query}"
    
    return {
        "name": clean_comp.title(),
        "portal_name": f"{clean_comp.title()} Careers",
        "apply_url": google_career_url,
        "home_url": company_site_url,
        "logo_url": f"https://icons.duckduckgo.com/ip3/{clean_comp.lower().replace(' ', '')}.com.ico",
        "ats_type": "DIRECT_CAREER",
        "description": f"Direct career portal search for {clean_comp.title()} matching {query}.",
        "is_official_portal": False
    }
