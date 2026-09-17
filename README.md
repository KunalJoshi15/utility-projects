# 🧰 Utility Projects

A multi-project monorepo containing developer tools, automation bots, and utility scripts.

---

## 📁 Repository Structure

```
utility-projects/
├── 📁 discord-job-bot/     # AI-powered Discord Job Search, Resume Review & Auto-Apply Bot
│   ├── bot/                # Discord UI modals, views, embeds & cogs
│   ├── config/             # Environment settings & configuration
│   ├── database/           # SQLite / PostgreSQL async models & migrations
│   ├── services/           # Gemini AI, job aggregation, visa directory & salary services
│   ├── scripts/            # GCP VM setup & deployment utilities
│   ├── tests/              # Pytest automated test suite
│   ├── deploy_to_vm.bat    # 1-click VM deployment script
│   └── README.md           # Full Discord Bot documentation & slash commands manual
│
├── 📁 utility-scripts/     # Automation scripts, scrapers & helper utilities
│   └── README.md
│
├── deploy_to_vm.bat        # Root convenience launcher to deploy discord-job-bot
└── README.md               # Repository overview
```

---

## 🚀 Projects Overview

### 1. [🤖 Discord Job Bot](./discord-job-bot/README.md)
An advanced, multi-user Discord bot powered by **Python**, **discord.py**, **Google Gemini AI**, and **Playwright**:
- **✨ Gemini AI Resume Audits & Job Fit**: Real-time evaluation of resume fit for target roles + Google XYZ bullet rewrites.
- **🔍 Natural Language & Tech Search**: Search jobs by typing descriptions (`/jobs prompt`) or via modal (`/jobs describe`).
- **🎯 Target Dream Company Tracking**: Monitor vacancies across Google, Microsoft, Amazon, Swiggy, etc.
- **🔔 Scheduled Job Alerts (Anti-Spam)**: Configurable frequency (1h–24h), batch sizing (1–10), and private DM delivery.
- **💰 Salary & Visa Intelligence**: AmbitionBox & Glassdoor benchmarks + verified EU/UK/US visa sponsorship directories.
- **☁️ 100% Free GCP Hosting ($0/mo)**: Permanent 24/7 hosting on GCP Free Tier.

👉 **[Read full Discord Bot documentation & slash command guide](./discord-job-bot/README.md)**

---

### 2. [🛠️ Utility Scripts](./utility-scripts/README.md)
Collection of standalone automation, data processing, and productivity tools.
