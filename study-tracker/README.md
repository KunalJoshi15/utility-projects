# 📚 Study Tracker & Interview Preparation Bot

An intelligent Discord bot and tracking service powered by **Python**, **discord.py**, **Google Gemini AI**, and **SQLAlchemy** designed to track career and interview preparation progress across **Microservices & Kubernetes**, **DSA**, **Low-Level Design (LLD)**, **High-Level Design (HLD)**, and **CS Fundamentals**.

---## 🌟 Key Features

1. **🎯 Multi-Track System & Candidate Enrollment**:
   - **Master Preparation Tracks**: 6 pre-seeded master curriculums covering **Master Career Prep** (43 modules across all domains), **Microservices & Kubernetes (10 modules)**, **DSA Patterns (10 modules)**, **LLD Machine Coding (10 modules)**, **HLD Distributed Systems (9 modules)**, and **CS Fundamentals (4 modules)**.
   - **📊 Excel (`.xlsx`/`.xls`) & CSV Ingestion**: Candidates can upload their custom Excel study schedules or syllabus spreadsheets directly to generate new tracks.
   - **👥 Multi-User Progress Isolation**: Any candidate can enroll in any track (and multiple tracks simultaneously). Each user's topic status (`TODO`, `IN_PROGRESS`, `COMPLETED`), confidence scores, and completion percentage are tracked 100% independently.
   - **Interactive UI**: 1-click Discord buttons to enroll and view live progress scorecards (`/track list`, `/track enroll`, `/track progress`, `/track toggle`, `/track create`, `/track my`).

2. **📝 Study Logging & Categorization**:
   - Log preparation across **Microservices & Kubernetes (☸️)**, **DSA (🧩)**, **LLD (🏗️)**, **HLD (🌐)**, **Core CS (💻)**, and **Mock Interviews (🎤)**.
   - Record problems/topics completed, study duration, confidence ratings (1-5 ⭐), notes, and complexity breakdowns.
   - Quick logging via slash commands or interactive popup modals (`/study quicklog`).

3. **☸️ Comprehensive Microservices & Kubernetes Roadmap**:
   - Dedicated structured curriculum tracking cloud-native distributed architecture:
     - **Kubernetes Core & Workloads**: Pods, Deployments, StatefulSets, Limits/Requests, Resource Quotas.
     - **Kubernetes Networking & Ingress**: ClusterIP, NodePort, LoadBalancer, Ingress Controllers, NetworkPolicies, CoreDNS.
     - **Kubernetes Storage & Config**: ConfigMaps, Secrets, PV/PVC, StorageClasses.
     - **K8s Auto-Scaling & Health Probes**: HPA (Horizontal Pod Autoscaler), VPA, Liveness/Readiness/Startup Probes, Graceful Shutdown.
     - **Helm & Packaging**: Charts, `values.yaml`, templates, release management, Kustomize.
     - **Docker & Container Runtime**: Multi-stage builds, rootless containers, Docker Compose, containerd.
     - **Distributed Transaction Patterns**: Saga Pattern (Orchestration vs Choreography), Transactional Outbox, CQRS, Idempotency keys.
     - **Communication & Service Mesh**: gRPC & Protobuf, Backend-For-Frontend (BFF), Service Mesh (Istio / Envoy), Circuit Breakers (Resilience4j).
     - **Observability & Distributed Tracing**: OpenTelemetry standard, Jaeger, Prometheus & Grafana, Centralized Logging (Loki/ELK).

4. **📁 File-Based Curriculum & Plan Ingestion**:
   - Ingest any syllabus file (`.md`, `.txt`, `.json`, `.yaml`, `.csv`) or paste curriculum outlines directly (`/study import_plan`).
   - Gemini AI parses and categorizes topics automatically into your personal roadmap.
   - **Topic Checklist & Progress**: Track individual topics as `TODO`, `IN_PROGRESS`, or `COMPLETED` (`/study topic_list`, `/study topic_toggle`).

5. **🎯 Target Exit Date & Daily Schedule Engine**:
   - Calculate structured daily/weekly timelines toward your target resignation/exit date (`/study schedule`).
   - Allocates morning & evening study slots (*what, when, and how to study*).
   - **🤖 Gemini AI Adaptation**: Modify your schedule anytime with natural language instructions (`/study schedule_adjust "I only have 1 hour on weekdays"`).
   - **👥 Social Schedule Forking**: Browse peer schedules and clone them into your profile with adapted target dates (`/study schedule_browse`, `/study schedule_clone`).

6. **📈 High-Resolution Graphical Progress Charts**:
   - Generates sleek dark-mode multi-panel analytics graphs (`/study chart`):
     - Daily study minutes (14-day history)
     - Cumulative study hours growth trajectory
     - Category distribution donut chart (Microservices, DSA, LLD, HLD, Core CS)
     - Syllabus topic completion progress bar

7. **⏰ Automated Inactivity & Streak Reminders**:
   - Background notifier delivers motivational DM reminders if you haven't logged prep by your configured evening reminder time (`/study reminders`).

8. **📚 Preparation Resources Catalog & Community Sharing**:
   - Built-in curated catalog of top industry guides (Kubernetes Official Docs, Microservices.io, Confluent Kafka, NeetCode 150, Striver's A2Z Sheet, Refactoring.Guru, System Design Primer).
   - **Community Submissions**: Share and upvote resources (`/study resource_add`, `/study resource_modal`, `/study upvote`).

9. **⏱️ Pomodoro Focus Timer**:
   - Dedicated focus timer (25m / 50m / custom) with interactive Discord buttons (`Complete & Log Session`, `Cancel`) and automatic progress logging.

10. **🤖 Gemini AI Interview Coach**:
    - **`/study plan <role> <company> [weeks]`**: Generates a tailored week-by-week study plan for your dream company.
    - **`/study quiz <topic> [difficulty]`**: Mock interview technical concept questions with immediate AI grading and ideal model answers.
    - **`/study revise`**: Spaced repetition queue suggesting topics that need revision.

11. **🏆 Server Study Leaderboard**:
    - Friendly server rankings by total study hours and problems solved (`/study leaderboard`).

---

## 📋 Slash Commands Manual

| Category | Command | Description |
|---|---|---|
| **🎯 Multi-Track System** | `/track list [category] [query]` | Browse Master & Community preparation tracks |
| | `/track enroll <track_id>` | Enroll in a track with separate, isolated personal progress |
| | `/track unenroll <track_id>` | Unenroll from a preparation track |
| | `/track progress [track_id] [user]` | View detailed visual scorecard and checklist for an enrolled track |
| | `/track toggle <track_id> <topic> [status] [confidence] [notes]` | Mark topic as Completed, In Progress, or To-Do in your track |
| | `/track create [title] [category] [description] [file] [text]` | 📊 Create a new track by uploading Excel (`.xlsx`/`.xls`), CSV, or text |
| | `/track my [user]` | View all tracks you are enrolled in with live completion % |
| **📝 Progress Tracking** | `/study log <category> <topic> [problems] [minutes] [confidence] [notes]` | Record a completed study session |
| | `/study quicklog` | Interactive popup modal for quick session logging |
| | `/study progress [user]` | View visual preparation scorecard & breakdown |
| | `/study chart [user]` | 📈 Render high-resolution graphical analytics image |
| | `/study streak` | View active daily study streak & milestone badge |
| | `/study roadmap [category]` | Browse curriculum for Microservices (K8s), DSA, LLD, HLD, Core CS |
| | `/study goals` | View and track your preparation milestones |
| | `/study profile [name] [target_role] [target_companies]` | Setup candidate profile (Discord ID auto-populated) |
| **📁 Syllabus & Topics** | `/study import_plan [file] [text]` | Ingest `.md`, `.txt`, `.json`, `.yaml`, or `.csv` files into your syllabus |
| | `/study topic_list [category]` | View interactive checklist of preparation topics |
| | `/study topic_toggle <topic_name> [status]` | Mark topic as Completed, In Progress, or To-Do |
| **🎯 Exit Scheduling & Sharing** | `/study schedule [user] [target_exit_date] [daily_slots]` | View/generate time-slotted study routine toward target exit date |
| | `/study schedule_adjust [instruction]` | Prompt Gemini AI to adapt your study schedule |
| | `/study schedule_browse [query]` | Browse community-shared public study schedules |
| | `/study schedule_clone <schedule_id> [exit_date]` | Clone/fork a peer's study schedule into your profile |
| | `/study reminders <enable> [hour_utc]` | Configure daily inactivity reminder notifications |
| **📚 Resource Catalog** | `/study resources [category] [topic]` | Browse curated and community learning resources |
| | `/study resource_add <category> <topic> <title> <url> [type]` | Submit a valuable preparation resource/tool to the catalog |
| | `/study resource_modal` | Interactive form popup to submit new resources |
| | `/study upvote <resource_id>` | Upvote a helpful preparation resource |
| **⏱️ Focus Timer** | `/study timer [duration] [task] [category]` | Start custom focus timer with 1-click auto-logging |
| | `/study pomodoro` | Start standard 25-minute Pomodoro study block |
| **🤖 Gemini AI Coach** | `/study plan <role> <company> [weeks]` | Generate week-by-week prep roadmap for your dream company |
| | `/study quiz <topic> [category] [difficulty]` | AI technical concept quiz with instant grading |
| | `/study revise` | Spaced repetition queue of topics needing review |
| **🏆 Community** | `/study leaderboard [limit]` | Server study champions leaderboard |
| **General** | `/help` | Complete bot manual and command reference |
| | `/status` | Latency, database, and AI status |Complete bot manual and command reference |
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
