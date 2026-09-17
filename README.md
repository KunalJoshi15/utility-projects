# 🚀 Discord Job Search, AI Resume Review & Auto-Apply Bot

An advanced, multi-user Discord bot powered by **Python**, **discord.py**, **Google Gemini AI**, and **Playwright** that allows Discord community members to:
1. **Upload Resumes** directly in Discord (PDF/DOCX).
2. **✨ Get Instant Gemini AI Resume Audits**: Comprehensive critique pointing out what is **not good in the resume**, missing metrics/numbers, ATS score (0-100), and recommended bullet-point rewrites using the Google XYZ method.
3. **🎯 Match Jobs from LinkedIn & Naukri**: Search for openings on **LinkedIn**, **Naukri**, and top ATS portals (Greenhouse, Lever) tailored directly to the candidate's skills and experience.
4. **⚡ Auto-Apply Directly**: Headless browser automation for **LinkedIn Easy Apply** and direct ATS career portals with verification screenshots.
5. **☁️ 100% Free GCP Hosting ($0 Cost)**: Engineered to run 24/7 permanently on the **Google Cloud Platform (GCP) Always Free Tier** (`e2-micro` + 4GB virtual swap space).

---

## ✨ Core Capabilities

- **✨ Google Gemini AI Resume Review (`/resume review`)**:
  - Highlights weak phrasing, passive voice, and lack of quantifiable business outcomes.
  - Scores ATS compliance and identifies missing high-demand tech keywords.
  - Provides side-by-side **Before & After bullet point rewrites**.
  - Actionable 3-step checklist to level up the candidate's resume.

- **🎯 Resume-to-Job Matching (`/jobs match`)**:
  - Automatically parses skills, tech stack, and target titles from the uploaded resume.
  - Queries **LinkedIn**, **Naukri**, and global aggregators for tailored openings.

- **⚡ Headless Auto-Apply Engine (Playwright)**:
  - **LinkedIn Easy Apply**: Automates multi-step forms, attaches resume PDF, and captures proof screenshots.
  - **ATS Career Portals**: Fills Greenhouse, Lever, and standard career applications.
  - **Proof of Submission**: Delivers screenshot verification directly in Discord.

- **👤 Multi-Tenant Security & Isolation**:
  - Multi-user isolation: Every user has an isolated candidate profile and resume vault.
  - Sensitive session credentials (e.g. LinkedIn `li_at` cookie) are encrypted with **Fernet (AES-128)**.

- **💰 100% Free Tier GCP Optimization**:
  - Configured for GCE `e2-micro` in free US regions (`us-central1`, `us-east1`, `us-west1`).
  - Automated **4GB swapfile memory** provisioning so that Playwright browser automation never crashes due to memory limits.
  - Local embedded SQLite database — zero external database costs.

---

## 📋 Slash Commands Reference

| Category | Command | Description |
|---|---|---|
| **✨ Gemini AI** | `/resume review` | In-depth AI critique of what's not good in resume + bullet rewrites |
| | `/resume parse` | Auto-extract skills and role to update your candidate profile |
| **🔍 Jobs** | `/jobs match` | Find LinkedIn & Naukri jobs matching your uploaded resume |
| | `/jobs search <query> [location]` | Search jobs across LinkedIn, Naukri, and portals with interactive pagination |
| | `/jobs view <job_id>` | View complete description and requirements |
| | `/jobs apply <job_id>` | Automatically submit application via Playwright |
| **👤 Profile** | `/profile resume <attachment>` | Drag-and-drop upload for candidate resume (PDF/DOCX) |
| | `/profile setup` | Interactive modal for contact info and portfolio links |
| | `/profile details` | Configure experience years, notice period, and sponsorship |
| | `/profile cookie` | Encrypted storage for LinkedIn session cookie |
| | `/profile view` | View your candidate profile status |
| **📊 Tracking** | `/applications list` | View history of submitted applications & screenshots |
| **General** | `/help` | Complete interactive usage manual |
| | `/status` | Latency, uptime, and system health |

---

## 🛠️ Local Quickstart

### 1. Clone repository & setup virtual environment
```bash
git clone https://github.com/your-username/discord-job-bot.git
cd discord-job-bot
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux/macOS
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure `.env`
Copy `.env.example` to `.env`:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
RAPIDAPI_KEY=
```

### 4. Run the Bot
```bash
python main.py
```

---

## ☁️ 100% Free GCP Cloud Deployment ($0 Cost)

Follow our [Complete GCP Free Tier Guide](file:///c:/Learning/Carrer-Prep/projects/discord-job-bot/scripts/gcp_deploy_guide.md).

**Quick Setup on GCP Compute Engine VM**:
1. Create an `e2-micro` VM in `us-central1`, `us-east1`, or `us-west1` with a 25GB standard persistent disk (Eligible for GCP Always Free).
2. SSH into the VM and run:
   ```bash
   git clone <repo-url> /opt/discord-job-bot
   cd /opt/discord-job-bot
   chmod +x scripts/setup_gcp_vm.sh
   ./scripts/setup_gcp_vm.sh
   nano .env # Add DISCORD_BOT_TOKEN and GEMINI_API_KEY
   sudo systemctl start discord-job-bot
   ```
