# 📚 Study Tracker & Interview Preparation Bot

An intelligent Discord bot and tracking service powered by **Python**, **discord.py**, **Google Gemini AI**, and **SQLAlchemy** designed to track career and interview preparation progress across **Microservices & Kubernetes**, **DSA**, **Low-Level Design (LLD)**, **High-Level Design (HLD)**, and **CS Fundamentals**.

---

## 🌟 Key Features

1. **📝 Study Logging & Categorization**:
   - Log preparation across **Microservices & Kubernetes (☸️)**, **DSA (🧩)**, **LLD (🏗️)**, **HLD (🌐)**, **Core CS (💻)**, and **Mock Interviews (🎤)**.
   - Record problems/topics completed, study duration, confidence ratings (1-5 ⭐), notes, and complexity breakdowns.
   - Quick logging via slash commands or interactive popup modals (`/study quicklog`).

2. **☸️ Comprehensive Microservices & Kubernetes Roadmap**:
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

3. **📚 Preparation Resources Catalog & Community Sharing**:
   - Built-in curated catalog of top industry guides (Kubernetes Official Docs, Microservices.io, Confluent Kafka, NeetCode 150, Striver's A2Z Sheet, Refactoring.Guru, System Design Primer).
   - **Community Submissions**: Anyone can share high-quality documentation, articles, practice sheets, cheatsheets, and repos (`/study resource_add` or `/study resource_modal`).
   - **Interactive Discovery & Upvoting**: Browse by domain/topic keyword (`/study resources`) and upvote the most helpful resources (`/study upvote`).

4. **📊 Visual Progress Scorecards & Analytics**:
   - Comprehensive progress cards with visual progress bars (`[████████░░] 80%`), total study hours, weekly momentum, and category breakdowns.
   - View your scorecard anytime with `/study progress`.

5. **🔥 Daily Study Streaks**:
   - Active daily streak tracking with milestone badges (7-day, 14-day, 30-day, 100-day).
   - Milestone progression tracker (`/study streak`).

6. **⏱️ Pomodoro Focus Timer**:
   - Dedicated focus timer (25m / 50m / custom) with interactive Discord buttons (`Complete & Log Session`, `Cancel`).
   - Automatically credits study hours directly upon completion.

7. **🤖 Gemini AI Interview Coach**:
   - **`/study plan <role> <company> [weeks]`**: Generates a tailored week-by-week study plan for your dream company.
   - **`/study quiz <topic> [difficulty]`**: Mock interview technical concept questions with immediate AI grading and ideal model answers.
   - **`/study revise`**: Spaced repetition queue suggesting topics that need revision based on confidence ratings and time elapsed.

8. **🏆 Server Study Leaderboard**:
   - Friendly server rankings by total study hours and problems solved (`/study leaderboard`).

---

## 📋 Slash Commands Manual

| Category | Command | Description |
|---|---|---|
| **📝 Progress Tracking** | `/study log <category> <topic> [problems] [minutes] [confidence] [problem_name] [notes]` | Record a completed study session with stats |
| | `/study quicklog` | Interactive popup modal for quick session logging |
| | `/study progress [user]` | View visual preparation scorecard & categorical breakdown |
| | `/study streak` | View active daily study streak & milestone badge |
| | `/study roadmap [category]` | Browse structured curriculum for Microservices (K8s), DSA, LLD, HLD & Core CS |
| | `/study goals` | View and track your preparation milestones |
| | `/study goal_create` | Modal to create custom milestone targets |
| | `/study profile [name] [target_role] [target_companies]` | Setup candidate profile (Discord ID auto-populated) |
| **📚 Resource Catalog** | `/study resources [category] [topic]` | Browse curated and community learning resources & guides |
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
