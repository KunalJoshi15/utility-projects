# 🚀 Discord Job Search, AI Resume Review & Auto-Apply Bot

An advanced, multi-user Discord bot powered by **Python**, **discord.py**, **Google Gemini AI**, and **Playwright** that allows Discord community members to:
1. **Upload Resumes** directly in Discord (PDF/DOCX).
2. **✨ Get Instant Gemini AI Resume Audits**: Comprehensive critique pointing out what is **not good in the resume**, missing metrics/numbers, ATS score (0-100), and recommended bullet-point rewrites using the Google XYZ method.
3. **🎯 Match Jobs & Track Target Dream Companies**: Search openings across **LinkedIn**, **Naukri**, and top ATS portals (Greenhouse, Lever) tailored to candidate skills or target companies (*Google, Microsoft, Amazon, Swiggy, Flipkart*).
4. **🔔 24/7 Automated Job Alerts**: Background monitoring scanning every 15 minutes for new openings matching country, city, payscale, target company, or visa sponsorship, tagging the candidate in their Discord channel.
5. **💰 Authentic Market Salary Benchmarks**: Integrated direct search links to **AmbitionBox**, **Glassdoor**, and **Levels.fyi** for roles and adjacent/similar positions without synthetic or fabricated numbers.
6. **🛂 International Visa Sponsorship & Relocation Directory**: Curated verified sponsors across **Germany (EU Blue Card)**, **Netherlands (Highly Skilled Migrant)**, **UK (Skilled Worker)**, **Canada (Global Talent Stream)**, **USA (H-1B/L-1)**, **Singapore (EP)**, and **UAE (Golden Visa)**.
7. **⚡ Auto-Apply Directly**: Headless browser automation for **LinkedIn Easy Apply** and direct ATS career portals with verification screenshots.
8. **☁️ 100% Free GCP Hosting ($0 Cost)**: Engineered to run 24/7 permanently on the **Google Cloud Platform (GCP) Always Free Tier** (`e2-micro` + 4GB virtual swap space).

---

## 📋 Complete Slash Commands Reference

| Category | Command | Description |
|---|---|---|
| **✨ Gemini AI** | `/resume review` | Deep AI critique of what's not good in your resume + Google XYZ bullet rewrites |
| | `/resume parse` | Auto-extract skills, tech stack, and role to update your candidate profile |
| **🔍 Job Search** | `/jobs search <query> [country] [city] [type] [salary] [company] [visa_sponsorship] [remote]` | Search live listings across LinkedIn, Naukri, Relocate.me, and Google Jobs |
| | `/jobs match` | Find openings matching your uploaded resume |
| | `/jobs companies [names]` | Search open vacancies across your target dream companies |
| | `/jobs view <job_id>` | View complete job description, requirements & live links |
| | `/jobs apply <job_id>` | Automatically submit application via Playwright headless browser |
| **💰 Salary Intelligence** | `/salary check <role> [company] [location]` | Look up authentic AmbitionBox & Glassdoor benchmarks for role & similar roles |
| | `/salary compare <role> [custom_companies]` | Compare paygrades across your dream companies side-by-side |
| **🛂 Visa Sponsorship** | `/visa companies [country]` | Browse top verified employers offering visa sponsorship in Germany, UK, NL, Canada, USA, SG, UAE |
| | `/visa jobs <role> [country]` | Search verified relocation & visa openings across Relocate.me, Landing.jobs & LinkedIn |
| | `/visa policy <company>` | Check official visa sponsorship track record & public government registry status |
| **🔔 24/7 Job Alerts** | `/alerts create <query> [country] [city] [company] [min_salary] [visa_sponsorship]` | Get tagged in your channel when new matching jobs appear |
| | `/alerts companies [role] [min_salary]` | Batch create 24/7 alerts for all your target dream companies |
| | `/alerts list` | View your active job alerts |
| | `/alerts delete <alert_id>` | Delete an active alert rule |
| | `/alerts check` | Trigger an immediate manual scan of all active alerts |
| **👤 Profile** | `/profile setup` | Interactive modal to configure contact info and location |
| | `/profile companies <names>` | Save your target dream companies (e.g. *Google, Microsoft, Amazon, Swiggy*) |
| | `/profile resume <attachment>` | Upload candidate resume (PDF/DOCX) for auto-applications & AI review |
| | `/profile details` | Set experience years, notice period, and sponsorship requirement |
| | `/profile cookie` | Encrypted storage for LinkedIn session cookie (Easy Apply) |
| | `/profile view` | View your saved candidate profile status |
| **📊 Tracking** | `/applications list` | View history of submitted applications & screenshots |
| **General** | `/help` | Complete interactive bot command manual |
| | `/status` | Latency, uptime, and system health |

---

## 🛠️ Local Development & Testing

### 1. Setup Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure `.env`
Create `.env` using `.env.example`:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Run Automated Tests
```powershell
.\.venv\Scripts\pytest.exe -v
```

### 4. Run Bot Locally
```powershell
python main.py
```

---

## 🚀 Deploying Local Changes to GCP VM

When you are done making and testing changes locally and want to publish them to your GCP VM instance (`instance-20260917-061701`):

### Option 1: 1-Click Deployment Script (Recommended)
Simply run the included batch script from your project root:
```powershell
.\deploy_to_vm.bat
```

### Option 2: Manual Terminal Commands

#### Step 1: Sync updated source files to GCP VM
```powershell
gcloud compute scp --recurse bot services database tests main.py docker-compose.yml instance-20260917-061701:/opt/discord-job-bot/ --zone=us-central1-a --project=seraphic-rune-366616
```

#### Step 2: Restart the bot service on the VM
```powershell
gcloud compute ssh instance-20260917-061701 --zone=us-central1-a --project=seraphic-rune-366616 --command="sudo systemctl restart discord-job-bot.service; sudo systemctl status discord-job-bot.service --no-pager"
```

### Option 3: Via Git (Push & Pull)
```powershell
# 1. Push local commits to GitHub:
git push -u origin main

# 2. Pull on GCP VM and restart:
gcloud compute ssh instance-20260917-061701 --zone=us-central1-a --project=seraphic-rune-366616 --command="cd /opt/discord-job-bot; git pull origin main; sudo systemctl restart discord-job-bot.service"
```

---

## ☁️ Initial GCP Free Tier VM Setup ($0/mo)

1. Create an `e2-micro` VM in `us-central1-a` with a 25GB standard disk.
2. Run initial setup script:
   ```bash
   git clone <repo-url> /opt/discord-job-bot
   cd /opt/discord-job-bot
   chmod +x scripts/setup_gcp_vm.sh
   ./scripts/setup_gcp_vm.sh
   sudo systemctl enable --now discord-job-bot.service
   ```
