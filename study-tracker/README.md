# 📚 Study Tracker & Interview Preparation Bot

An intelligent Discord bot and tracking service powered by **Python**, **discord.py**, **Google Gemini AI**, and **SQLAlchemy** designed to track career and interview preparation progress across DSA, Low-Level Design (LLD), High-Level Design (HLD), and CS Fundamentals.

---

## 🌟 Key Features

1. **📝 Study Logging & Categorization**:
   - Log preparation across **DSA**, **LLD**, **HLD**, **Core CS**, and **Mock Interviews**.
   - Record problems solved, study duration, confidence ratings (1-5 ⭐), notes, and complexity breakdowns.
   - Quick logging via slash commands or interactive popup modals (`/study quicklog`).

2. **📊 Visual Progress Scorecards & Analytics**:
   - Comprehensive progress cards with visual progress bars (`[████████░░] 80%`), total study hours, weekly momentum, and category breakdowns.
   - View your scorecard anytime with `/study progress`.

3. **🔥 Daily Study Streaks**:
   - Active daily streak tracking with milestone badges (7-day, 14-day, 30-day, 100-day).
   - Milestone progression tracker (`/study streak`).

4. **🗺️ Curated Topic Roadmaps**:
   - Built-in structured curriculum for:
     - **🧩 DSA**: Arrays, Sliding Window, Two Pointers, Trees, Graphs, Dynamic Programming.
     - **🏗️ LLD**: SOLID principles, Design Patterns, Parking Lot, Tic-Tac-Toe, Rate Limiter, Splitwise.
     - **🌐 HLD**: Distributed Systems, Caching (Redis), Sharding, Messaging (Kafka), URL Shortener, Chat Apps.
     - **💻 Core CS**: Concurrency, Multi-threading, OS, DBMS Transactions (ACID), Computer Networks.

5. **⏱️ Pomodoro Focus Timer**:
   - Dedicated focus timer (25m / 50m / custom) with interactive Discord buttons (`Complete & Log Session`, `Cancel`).
   - Automatically credits study hours directly upon completion.

6. **🤖 Gemini AI Interview Coach**:
   - **`/study plan <role> <company> [weeks]`**: Generates a tailored week-by-week study plan for your dream company.
   - **`/study quiz <topic> [difficulty]`**: Mock interview technical concept questions with immediate AI grading and ideal model answers.
   - **`/study revise`**: Spaced repetition queue suggesting topics that need revision based on confidence ratings and time elapsed.

7. **🏆 Server Study Leaderboard**:
   - Friendly server rankings by total study hours and problems solved (`/study leaderboard`).

---

## 📋 Slash Commands Manual

| Category | Command | Description |
|---|---|---|
| **📝 Progress Tracking** | `/study log <category> <topic> [problems] [minutes] [confidence] [problem_name] [notes]` | Record a completed study session with stats |
| | `/study quicklog` | Interactive popup modal for quick session logging |
| | `/study progress [user]` | View visual preparation scorecard & categorical breakdown |
| | `/study streak` | View active daily study streak & milestone badge |
| | `/study roadmap [category]` | Browse structured curriculum for DSA, LLD, HLD & Core CS |
| | `/study goals` | View and track your preparation milestones |
| | `/study goal_create` | Modal to create custom milestone targets |
| | `/study profile [name] [target_role] [target_companies]` | Setup/update candidate profile (Discord ID auto-populated) |
| **⏱️ Focus Timer** | `/study timer [duration] [task] [category]` | Start custom focus timer with 1-click auto-logging |
| | `/study pomodoro` | Start standard 25-minute Pomodoro study block |
| **🤖 Gemini AI Coach** | `/study plan <role> <company> [weeks]` | Generate week-by-week prep roadmap for your dream company |
| | `/study quiz <topic> [category] [difficulty]` | AI technical concept quiz with instant grading |
| | `/study revise` | Spaced repetition queue of topics needing review |
| **🏆 Community** | `/study leaderboard [limit]` | Server study champions leaderboard |
| **General** | `/help` | Complete bot manual and command reference |
| | `/status` | Latency, database, and AI status |

---

## 🛠️ Local Development & Testing

### 1. Setup Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`
Create `.env` using `.env.example`:
```env
STUDY_BOT_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Run Automated Tests
```powershell
pytest -v
```

### 4. Run Bot Locally
```powershell
python main.py
```
