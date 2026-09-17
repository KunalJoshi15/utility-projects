# 🧰 Developer & Career Prep Projects

A multi-project monorepo containing AI-powered Discord bots and developer productivity services.

---

## 📁 Repository Structure

```
utility-projects/
│
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
├── 📁 study-tracker/       # Interview Preparation, Progress & AI Coaching Bot
│   ├── bot/                # UI embeds, modals, views & cogs (Study, Pomodoro, AI Coach)
│   ├── config/             # Environment settings & configuration
│   ├── database/           # Async models (Logs, Goals, Streaks, Pomodoro)
│   ├── services/           # Study analytics, roadmaps & Gemini AI coach services
│   ├── tests/              # Automated test suite
│   ├── deploy_to_vm.bat    # 1-click VM deployment script
│   └── README.md           # Full Study Tracker documentation & slash command guide
│
├── deploy_to_vm.bat        # Root deployment launcher for discord-job-bot
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

### 2. [📚 Study Tracker Bot](./study-tracker/README.md)
A dedicated interview preparation and career progress tracking bot:
- **📝 Study Logging & Roadmaps**: Log preparation across DSA, LLD, HLD, and Core CS with confidence scores & notes.
- **📊 Visual Progress Scorecards**: Progress bars, weekly momentum, and hours breakdown (`/study progress`).
- **🔥 Daily Study Streaks**: Daily streak tracking with milestone badges (`/study streak`).
- **⏱️ Pomodoro Focus Timer**: 25m/custom study blocks with 1-click auto-logging (`/study timer`, `/study pomodoro`).
- **🤖 Gemini AI Interview Coach**: AI weekly study plans, mock interview concept quizzes with grading, and spaced repetition revision queue (`/study plan`, `/study quiz`, `/study revise`).
- **🏆 Server Study Leaderboard**: Track and compete with peers on preparation time and problems solved.

👉 **[Read full Study Tracker documentation & slash command guide](./study-tracker/README.md)**
