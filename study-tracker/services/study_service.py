import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta, date
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    UserStudyProfile,
    StudyLog,
    StudyGoal,
    StudyStreak,
    StudyCategory
)

logger = logging.getLogger(__name__)

CURATED_ROADMAPS = {
    "DSA": {
        "title": "🧩 Data Structures & Algorithms (Top Interview Roadmap)",
        "description": "Essential patterns for top tech coding interviews (LeetCode & NeetCode style)",
        "topics": [
            {"name": "Arrays & Hashing", "key_problems": ["Two Sum", "Group Anagrams", "Top K Frequent Elements", "Product of Array Except Self"]},
            {"name": "Two Pointers & Sliding Window", "key_problems": ["Valid Palindrome", "3Sum", "Container With Most Water", "Longest Substring Without Repeating Characters"]},
            {"name": "Stack & Monotonic Stack", "key_problems": ["Valid Parentheses", "Min Stack", "Daily Temperatures", "Largest Rectangle in Histogram"]},
            {"name": "Binary Search", "key_problems": ["Binary Search", "Search in Rotated Sorted Array", "Find Minimum in Rotated Sorted Array", "Koko Eating Bananas"]},
            {"name": "Linked List & Fast/Slow Pointers", "key_problems": ["Reverse Linked List", "Merge Two Sorted Lists", "Reorder List", "LRU Cache"]},
            {"name": "Trees & BST", "key_problems": ["Invert Binary Tree", "Lowest Common Ancestor of BST", "Binary Tree Level Order Traversal", "Serialize & Deserialize Binary Tree"]},
            {"name": "Tries & Backtracking", "key_problems": ["Implement Trie", "Subsets", "Combination Sum", "Word Search"]},
            {"name": "Heap & Priority Queue", "key_problems": ["Kth Largest Element in Array", "Task Scheduler", "Find Median from Data Stream"]},
            {"name": "Graphs (BFS, DFS, Dijkstra)", "key_problems": ["Number of Islands", "Clone Graph", "Course Schedule", "Pacific Atlantic Water Flow", "Network Delay Time"]},
            {"name": "Dynamic Programming (1D & 2D)", "key_problems": ["Climbing Stairs", "Coin Change", "Longest Increasing Subsequence", "0/1 Knapsack", "Edit Distance"]}
        ]
    },
    "LLD": {
        "title": "🏗️ Low-Level Design & Object-Oriented Architecture",
        "description": "SOLID principles, design patterns, and classic machine coding interview problems",
        "topics": [
            {"name": "SOLID Principles & Clean Code", "key_problems": ["Single Responsibility", "Open-Closed", "Liskov Substitution", "Interface Segregation", "Dependency Inversion"]},
            {"name": "Creational Patterns", "key_problems": ["Factory Method & Abstract Factory", "Singleton & Thread-Safe Double-Checked Locking", "Builder Pattern", "Prototype"]},
            {"name": "Behavioral Patterns", "key_problems": ["Observer Pattern", "Strategy Pattern", "Command Pattern", "State Pattern", "Iterator Pattern"]},
            {"name": "Structural Patterns", "key_problems": ["Decorator Pattern", "Adapter Pattern", "Facade Pattern", "Proxy Pattern", "Composite Pattern"]},
            {"name": "Classic Problem: Parking Lot System", "key_problems": ["Multi-floor parking building", "Vehicle types (Bike/Car/Truck)", "Slot allocation strategies", "Ticketing & payment gate"]},
            {"name": "Classic Problem: Tic-Tac-Toe Game Engine", "key_problems": ["N x N Board", "Winning condition validation (O(1))", "Piece types", "Minimax / Bot AI player"]},
            {"name": "Classic Problem: Rate Limiter", "key_problems": ["Token Bucket Algorithm", "Leaky Bucket Algorithm", "Sliding Window Counter", "Fixed Window Counter"]},
            {"name": "Classic Problem: Elevator Management System", "key_problems": ["Multi-elevator dispatch algorithm", "SCAN / LOOK algorithm", "State handling (Moving/Idle/Door open)"]},
            {"name": "Classic Problem: Splitwise Expense Sharing", "key_problems": ["Equal, Exact, Percentage splits", "Debt simplification algorithm", "Balance sheet management"]},
            {"name": "Classic Problem: Snake & Ladders / Chess Game", "key_problems": ["Board representation", "Dice rolling", "Piece movement validation", "Check/Checkmate detection"]}
        ]
    },
    "HLD": {
        "title": "🌐 High-Level Design & Distributed Systems",
        "description": "Scalable architectures, distributed storage, caching, and large-scale system design",
        "topics": [
            {"name": "Core Fundamentals", "key_problems": ["CAP Theorem & PACELC", "Consistent Hashing", "Load Balancers (L4 vs L7, Nginx/HAProxy)", "Forward vs Reverse Proxy"]},
            {"name": "Caching Strategies", "key_problems": ["Cache-Aside, Write-Through, Write-Back", "Eviction Policies (LRU, LFU, ARC)", "Redis & Memcached architectures", "Thundering Herd Problem"]},
            {"name": "Databases & Partitioning", "key_problems": ["SQL vs NoSQL trade-offs", "Horizontal Sharding & Re-sharding", "Read Replicas & Master-Slave replication", "Database Indexing (B-Tree vs LSM-Tree)"]},
            {"name": "Messaging & Streaming", "key_problems": ["Apache Kafka (Partitions, Consumer Groups)", "RabbitMQ (AMQP exchanges)", "Idempotent consumers", "Dead Letter Queues"]},
            {"name": "Classic System: URL Shortener (TinyURL / Bitly)", "key_problems": ["Base62 encoding", "MD5 / MurmurHash with collision resolution", "Redis caching layer", "Database schema & high read-to-write ratio"]},
            {"name": "Classic System: Real-Time Chat System (WhatsApp / Slack)", "key_problems": ["WebSocket connections & Gateway servers", "Message ordering & delivery receipts (Single/Double tick)", "Group chat fan-out", "Cassandra message store"]},
            {"name": "Classic System: Rate Limiter & API Gateway", "key_problems": ["Distributed Redis Token Bucket", "Race condition mitigation (Lua scripts)", "HTTP 429 Retry-After headers"]},
            {"name": "Classic System: Video Streaming Service (YouTube / Netflix)", "key_problems": ["Video chunking & adaptive bitrate streaming (HLS/DASH)", "CDN geo-distribution", "Metadata database & search indexing"]},
            {"name": "Classic System: Notification System", "key_problems": ["Multi-channel dispatch (APNS, FCM, Email, SMS)", "Rate limiting & user notification preferences", "Message deduplication & priority queues"]}
        ]
    },
    "MICROSERVICES": {
        "title": "⚡ Microservices Architecture & Kubernetes Ecosystem",
        "description": "Cloud-native distributed services, container orchestration, Kubernetes, Service Mesh, and Event-Driven systems",
        "topics": [
            {
                "name": "Kubernetes Core & Workloads",
                "key_problems": [
                    "Pods, ReplicaSets & Deployments",
                    "StatefulSets & DaemonSets",
                    "Jobs & CronJobs",
                    "Resource Limits, Requests & QoS Classes"
                ]
            },
            {
                "name": "Kubernetes Networking & Ingress",
                "key_problems": [
                    "ClusterIP vs NodePort vs LoadBalancer",
                    "Ingress Controllers (Nginx, Traefik, ALB)",
                    "NetworkPolicies (Micro-segmentation)",
                    "CoreDNS & Service Discovery inside K8s"
                ]
            },
            {
                "name": "Kubernetes Storage & Config",
                "key_problems": [
                    "ConfigMaps & Secrets management",
                    "PersistentVolumes (PV) & PVCs",
                    "StorageClasses & Dynamic Provisioning",
                    "Secret rotation & HashiCorp Vault integration"
                ]
            },
            {
                "name": "Kubernetes Auto-Scaling & Health Probes",
                "key_problems": [
                    "Horizontal Pod Autoscaler (HPA) with custom metrics",
                    "Vertical Pod Autoscaler (VPA) & Cluster Autoscaler",
                    "Liveness, Readiness & Startup Probes",
                    "Graceful Pod Termination & SIGTERM handling"
                ]
            },
            {
                "name": "Helm & Packaging for K8s",
                "key_problems": [
                    "Helm Chart structure & templates",
                    "values.yaml overrides & environments",
                    "Helm lifecycle hooks & rollback management",
                    "Kustomize vs Helm comparison"
                ]
            },
            {
                "name": "Docker & Container Runtime",
                "key_problems": [
                    "Multi-stage Docker builds & minimal images",
                    "Container security & non-root execution",
                    "Docker Compose for local multi-service testing",
                    "containerd & OCI runtime standards"
                ]
            },
            {
                "name": "Distributed Patterns (Saga, CQRS, Outbox)",
                "key_problems": [
                    "Saga Pattern (Choreography vs Orchestration)",
                    "Transactional Outbox Pattern with Debezium CDC",
                    "CQRS (Command Query Responsibility Segregation)",
                    "Idempotency Keys & Deduplication in Microservices"
                ]
            },
            {
                "name": "Communication & API Gateways",
                "key_problems": [
                    "gRPC & Protocol Buffers vs REST vs GraphQL",
                    "API Gateway & BFF (Backend for Frontend) pattern",
                    "Service Mesh (Istio / Envoy sidecars & mTLS)",
                    "Circuit Breakers & Rate Limiting (Resilience4j)"
                ]
            },
            {
                "name": "Observability & Distributed Tracing",
                "key_problems": [
                    "OpenTelemetry (Traces, Metrics, Logs)",
                    "Distributed Tracing with Jaeger / Zipkin (TraceId, SpanId)",
                    "Prometheus & Grafana for SLIs/SLOs monitoring",
                    "Centralized Logging (ELK & Grafana Loki)"
                ]
            }
        ]
    },
    "CORE_CS": {
        "title": "💻 Computer Science Fundamentals & Concurrency",
        "description": "Operating systems, DBMS internals, networking, and multi-threading",
        "topics": [
            {"name": "Concurrency & Multi-Threading", "key_problems": ["Threads vs Processes", "Mutex, Semaphores & ReentrantLock", "Deadlock detection & prevention", "Java Memory Model & volatile keyword"]},
            {"name": "Database Internals & Transactions", "key_problems": ["ACID properties in depth", "Transaction Isolation Levels (Read Committed, Repeatable Read, Serializable)", "Optimistic vs Pessimistic Locking", "2-Phase Commit (2PC)"]},
            {"name": "Operating Systems", "key_problems": ["Virtual Memory & Paging", "Context Switching overhead", "CPU Scheduling algorithms", "File Systems & Inodes"]},
            {"name": "Computer Networks", "key_problems": ["TCP 3-Way Handshake & 4-Way Teardown", "TCP vs UDP", "HTTPS / TLS Handshake & Certificates", "DNS Resolution flow", "HTTP/1.1 vs HTTP/2 vs HTTP/3 (QUIC)"]}
        ]
    }
}

CURATED_RESOURCES = [
    # Kubernetes & Microservices
    {
        "category": "MICROSERVICES",
        "topic": "Kubernetes Architecture & Core Concepts",
        "title": "Kubernetes Official Interactive Tutorials & Basics",
        "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/",
        "resource_type": "DOCUMENTATION",
        "description": "Interactive browser-based tutorial covering Pods, Deployments, Services, and scaling."
    },
    {
        "category": "MICROSERVICES",
        "topic": "Microservices Patterns",
        "title": "Microservices.io Pattern Language by Chris Richardson",
        "url": "https://microservices.io/patterns/index.html",
        "resource_type": "ARTICLE",
        "description": "Industry standard pattern catalog covering Saga, CQRS, API Gateway, Service Mesh, and Circuit Breaker."
    },
    {
        "category": "MICROSERVICES",
        "topic": "Kubernetes Networking & Ingress",
        "title": "Kubernetes Ingress & Service Networking Deep Dive",
        "url": "https://kubernetes.io/docs/concepts/services-networking/",
        "resource_type": "DOCUMENTATION",
        "description": "Comprehensive explanation of ClusterIP, NodePort, LoadBalancer, and Ingress routing."
    },
    {
        "category": "MICROSERVICES",
        "topic": "Distributed Tracing & Observability",
        "title": "OpenTelemetry Official Documentation & CNCF Standards",
        "url": "https://opentelemetry.io/docs/",
        "resource_type": "DOCUMENTATION",
        "description": "Unified standard for traces, metrics, and logs in cloud-native microservices."
    },
    {
        "category": "MICROSERVICES",
        "topic": "Event-Driven Microservices with Kafka",
        "title": "Confluent Kafka Microservices Architecture Guide",
        "url": "https://developer.confluent.io/learn/kafka-microservices/",
        "resource_type": "ARTICLE",
        "description": "Event sourcing, CQRS, and message streaming with Apache Kafka."
    },
    # DSA
    {
        "category": "DSA",
        "topic": "DSA Patterns & LeetCode Roadmaps",
        "title": "NeetCode 150 & Blind 75 Interactive Practice Roadmap",
        "url": "https://neetcode.io/roadmap",
        "resource_type": "PRACTICE",
        "description": "Structured curriculum covering all top coding interview patterns with video solutions."
    },
    {
        "category": "DSA",
        "topic": "Algorithms & Problem Solving",
        "title": "Striver's A2Z DSA Sheet",
        "url": "https://takeuforward.org/strivers-a2z-dsa-course/strivers-a2z-dsa-course-sheet-2/",
        "resource_type": "PRACTICE",
        "description": "Comprehensive end-to-end DSA preparation sheet."
    },
    # LLD
    {
        "category": "LLD",
        "topic": "Design Patterns & SOLID",
        "title": "Refactoring.Guru Design Patterns & SOLID Guide",
        "url": "https://refactoring.guru/design-patterns",
        "resource_type": "CHEATSHEET",
        "description": "Visual, code-rich guide to Creational, Structural, and Behavioral design patterns."
    },
    # HLD
    {
        "category": "HLD",
        "topic": "System Design Fundamentals",
        "title": "The System Design Primer by Donne Martin",
        "url": "https://github.com/donnemartin/system-design-primer",
        "resource_type": "REPO",
        "description": "The open-source Bible for large-scale distributed system design interviews."
    }
]

class StudyService:
    async def get_or_create_profile(self, db: AsyncSession, discord_id: str, username: Optional[str] = None, display_name: Optional[str] = None) -> UserStudyProfile:
        """Fetch or initialize candidate study profile with auto-populated Discord user ID."""
        result = await db.execute(
            select(UserStudyProfile).where(UserStudyProfile.discord_id == str(discord_id))
        )
        profile = result.scalars().first()
        if not profile:
            profile = UserStudyProfile(
                discord_id=str(discord_id),
                username=username or "User",
                display_name=display_name or username or "User"
            )
            db.add(profile)
            await db.flush()
        return profile

    async def update_profile(
        self,
        db: AsyncSession,
        discord_id: str,
        username: Optional[str] = None,
        display_name: Optional[str] = None,
        target_role: Optional[str] = None,
        target_companies: Optional[str] = None,
        target_interview_date: Optional[str] = None,
        daily_goal_minutes: Optional[int] = None,
        daily_goal_problems: Optional[int] = None,
    ) -> UserStudyProfile:
        """Update candidate study profile."""
        profile = await self.get_or_create_profile(db, discord_id, username, display_name)
        if display_name:
            profile.display_name = display_name
        if target_role:
            profile.target_role = target_role
        if target_companies:
            profile.target_companies = target_companies
        if target_interview_date:
            profile.target_interview_date = target_interview_date
        if daily_goal_minutes is not None:
            profile.daily_goal_minutes = daily_goal_minutes
        if daily_goal_problems is not None:
            profile.daily_goal_problems = daily_goal_problems

        await db.commit()
        await db.refresh(profile)
        return profile

    async def log_session(
        self,
        db: AsyncSession,
        discord_id: str,
        category: str,
        topic: str,
        subtopic_or_problem: Optional[str] = None,
        duration_minutes: int = 30,
        problems_solved: int = 1,
        confidence_score: int = 4,
        notes: Optional[str] = None,
        external_link: Optional[str] = None,
        username: Optional[str] = None
    ) -> StudyLog:
        """Log a study session, auto-update streaks and increment matching goal counters."""
        await self.get_or_create_profile(db, discord_id, username)

        cat_normalized = category.upper() if category.upper() in ["DSA", "LLD", "HLD", "MICROSERVICES", "CORE_CS", "MOCK_INTERVIEW", "CUSTOM"] else "DSA"
        conf = max(1, min(5, confidence_score))
        dur = max(1, duration_minutes)
        probs = max(0, problems_solved)

        log = StudyLog(
            discord_id=str(discord_id),
            category=cat_normalized,
            topic=topic.strip(),
            subtopic_or_problem=subtopic_or_problem.strip() if subtopic_or_problem else None,
            duration_minutes=dur,
            problems_solved=probs,
            confidence_score=conf,
            notes=notes.strip() if notes else None,
            external_link=external_link.strip() if external_link else None,
            logged_at=datetime.now(timezone.utc)
        )
        db.add(log)

        # Update streak
        await self._update_user_streak(db, str(discord_id))

        # Update matching active goals
        await self._increment_goal_progress(db, str(discord_id), cat_normalized, probs, dur)

        await db.commit()
        await db.refresh(log)
        return log

    async def _update_user_streak(self, db: AsyncSession, discord_id: str) -> StudyStreak:
        """Calculate and update study streak (today vs yesterday)."""
        today_str = date.today().isoformat()
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()

        result = await db.execute(
            select(StudyStreak).where(StudyStreak.discord_id == discord_id)
        )
        streak = result.scalars().first()

        if not streak:
            streak = StudyStreak(
                discord_id=discord_id,
                current_streak=1,
                longest_streak=1,
                last_study_date=today_str,
                total_days_studied=1
            )
            db.add(streak)
            await db.flush()
            return streak

        if streak.last_study_date == today_str:
            # Already studied today, streak stays the same
            return streak

        if streak.last_study_date == yesterday_str:
            # Continued streak!
            streak.current_streak += 1
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            streak.total_days_studied += 1
            streak.last_study_date = today_str
        else:
            # Streak broken
            streak.current_streak = 1
            streak.total_days_studied += 1
            streak.last_study_date = today_str

        await db.flush()
        return streak

    async def _increment_goal_progress(self, db: AsyncSession, discord_id: str, category: str, problems: int, minutes: int):
        """Auto-increment active goal counters."""
        result = await db.execute(
            select(StudyGoal).where(
                StudyGoal.discord_id == discord_id,
                StudyGoal.is_completed == False
            )
        )
        goals = result.scalars().all()
        for g in goals:
            if g.category.upper() == category.upper() or g.category.upper() == "ALL":
                if g.unit == "problems" and problems > 0:
                    g.current_count += problems
                elif g.unit == "hours" and minutes > 0:
                    g.current_count += round(minutes / 60.0, 1)
                elif g.unit == "minutes":
                    g.current_count += minutes

                if g.current_count >= g.target_count:
                    g.is_completed = True

    async def get_streak_status(self, db: AsyncSession, discord_id: str) -> Dict[str, Any]:
        """Fetch streak metrics."""
        result = await db.execute(
            select(StudyStreak).where(StudyStreak.discord_id == str(discord_id))
        )
        streak = result.scalars().first()
        today_str = date.today().isoformat()
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()

        if not streak:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "total_days_studied": 0,
                "studied_today": False,
                "last_study_date": None
            }

        studied_today = streak.last_study_date == today_str
        # If last study was neither today nor yesterday, streak is currently 0
        active_streak = streak.current_streak if (streak.last_study_date in (today_str, yesterday_str)) else 0

        return {
            "current_streak": active_streak,
            "longest_streak": streak.longest_streak,
            "total_days_studied": streak.total_days_studied,
            "studied_today": studied_today,
            "last_study_date": streak.last_study_date
        }

    async def get_user_progress_summary(self, db: AsyncSession, discord_id: str) -> Dict[str, Any]:
        """Compute aggregated study statistics, breakdown by category, weekly hours, and confidence."""
        profile = await self.get_or_create_profile(db, discord_id)
        streak_data = await self.get_streak_status(db, discord_id)

        # Query all logs
        logs_query = await db.execute(
            select(StudyLog)
            .where(StudyLog.discord_id == str(discord_id))
            .order_by(StudyLog.logged_at.desc())
        )
        logs = list(logs_query.scalars().all())

        total_minutes = sum(l.duration_minutes for l in logs)
        total_hours = round(total_minutes / 60.0, 1)
        total_problems = sum(l.problems_solved for l in logs)

        # Category breakdown
        category_breakdown = {}
        for cat in ["DSA", "LLD", "HLD", "CORE_CS", "MOCK_INTERVIEW", "CUSTOM"]:
            cat_logs = [l for l in logs if l.category == cat]
            category_breakdown[cat] = {
                "total_hours": round(sum(l.duration_minutes for l in cat_logs) / 60.0, 1),
                "problems_solved": sum(l.problems_solved for l in cat_logs),
                "sessions_count": len(cat_logs),
                "avg_confidence": round(sum(l.confidence_score for l in cat_logs) / len(cat_logs), 1) if cat_logs else 0
            }

        # Last 7 days study hours
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_logs = [l for l in logs if l.logged_at.replace(tzinfo=timezone.utc) >= seven_days_ago]
        weekly_hours = round(sum(l.duration_minutes for l in recent_logs) / 60.0, 1)
        weekly_problems = sum(l.problems_solved for l in recent_logs)

        # Recent 5 topics
        recent_topics = [
            {
                "category": l.category,
                "topic": l.topic,
                "subtopic": l.subtopic_or_problem or l.topic,
                "confidence": l.confidence_score,
                "minutes": l.duration_minutes,
                "date": l.logged_at.strftime("%b %d")
            }
            for l in logs[:5]
        ]

        return {
            "user_id": discord_id,
            "display_name": profile.display_name or profile.username or "Candidate",
            "target_role": profile.target_role or "Software Engineer",
            "target_companies": profile.target_companies or "Google, Microsoft, Amazon",
            "target_interview_date": profile.target_interview_date,
            "total_hours": total_hours,
            "total_problems": total_problems,
            "weekly_hours": weekly_hours,
            "weekly_problems": weekly_problems,
            "total_sessions": len(logs),
            "streak": streak_data,
            "categories": category_breakdown,
            "recent_topics": recent_topics
        }

    async def create_goal(
        self,
        db: AsyncSession,
        discord_id: str,
        title: str,
        target_count: int,
        category: str = "DSA",
        unit: str = "problems",
        deadline: Optional[str] = None
    ) -> StudyGoal:
        """Create a targeted preparation goal."""
        goal = StudyGoal(
            discord_id=str(discord_id),
            title=title.strip(),
            category=category.upper(),
            target_count=max(1, target_count),
            current_count=0,
            unit=unit.lower(),
            deadline=deadline.strip() if deadline else None,
            is_completed=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
        return goal

    async def get_goals(self, db: AsyncSession, discord_id: str) -> List[StudyGoal]:
        """Fetch all goals for user."""
        result = await db.execute(
            select(StudyGoal)
            .where(StudyGoal.discord_id == str(discord_id))
            .order_by(StudyGoal.is_completed.asc(), StudyGoal.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_goal(self, db: AsyncSession, goal_id: int, discord_id: str) -> bool:
        """Delete a goal."""
        result = await db.execute(
            select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.discord_id == str(discord_id))
        )
        goal = result.scalars().first()
        if goal:
            await db.delete(goal)
            await db.commit()
            return True
        return False

    async def get_leaderboard(self, db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch server-wide study leaderboard by total hours & problems solved."""
        profiles_res = await db.execute(select(UserStudyProfile))
        profiles = profiles_res.scalars().all()

        board = []
        for p in profiles:
            logs_res = await db.execute(
                select(StudyLog).where(StudyLog.discord_id == p.discord_id)
            )
            logs = logs_res.scalars().all()
            total_minutes = sum(l.duration_minutes for l in logs)
            total_problems = sum(l.problems_solved for l in logs)

            streak_data = await self.get_streak_status(db, p.discord_id)

            if total_minutes > 0 or total_problems > 0:
                board.append({
                    "discord_id": p.discord_id,
                    "name": p.display_name or p.username or "Candidate",
                    "total_hours": round(total_minutes / 60.0, 1),
                    "total_problems": total_problems,
                    "streak_days": streak_data["current_streak"]
                })

        board.sort(key=lambda x: (x["total_hours"], x["total_problems"]), reverse=True)
        return board[:limit]

    async def add_resource(
        self,
        db: AsyncSession,
        category: str,
        topic: str,
        title: str,
        url: str,
        resource_type: str = "ARTICLE",
        description: Optional[str] = None,
        added_by_discord_id: Optional[str] = None,
        added_by_name: Optional[str] = None
    ) -> StudyResource:
        """Add a learning resource or tutorial link."""
        from database.models import StudyResource
        res = StudyResource(
            category=category.upper(),
            topic=topic.strip(),
            title=title.strip(),
            url=url.strip(),
            resource_type=resource_type.upper(),
            description=description.strip() if description else None,
            added_by_discord_id=added_by_discord_id or "COMMUNITY",
            added_by_name=added_by_name or "Community Member",
            is_verified=True,
            upvotes=1,
            created_at=datetime.now(timezone.utc)
        )
        db.add(res)
        await db.commit()
        await db.refresh(res)
        return res

    async def get_resources(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """Fetch curated and user-submitted resources."""
        from database.models import StudyResource
        # Ensure default curated resources are seeded in DB
        await self.seed_default_resources(db)

        stmt = select(StudyResource)
        if category:
            stmt = stmt.where(StudyResource.category == category.upper())
        if topic:
            stmt = stmt.where(StudyResource.topic.ilike(f"%{topic}%"))
        stmt = stmt.order_by(StudyResource.upvotes.desc(), StudyResource.created_at.desc()).limit(limit)

        result = await db.execute(stmt)
        db_resources = list(result.scalars().all())

        return [
            {
                "id": r.id,
                "category": r.category,
                "topic": r.topic,
                "title": r.title,
                "url": r.url,
                "type": r.resource_type,
                "description": r.description or "Verified prep resource",
                "added_by": r.added_by_name or "Curated",
                "upvotes": r.upvotes
            }
            for r in db_resources
        ]

    async def upvote_resource(self, db: AsyncSession, resource_id: int):
        """Upvote a resource and return updated resource."""
        from database.models import StudyResource
        result = await db.execute(select(StudyResource).where(StudyResource.id == resource_id))
        res = result.scalars().first()
        if res:
            res.upvotes += 1
            await db.commit()
            await db.refresh(res)
            return res
        return None

    async def seed_default_resources(self, db: AsyncSession):
        """Seed initial curated resources if database table is empty."""
        from database.models import StudyResource
        count_res = await db.execute(select(func.count(StudyResource.id)))
        count = count_res.scalar() or 0
        if count == 0:
            for item in CURATED_RESOURCES:
                db_item = StudyResource(
                    category=item["category"],
                    topic=item["topic"],
                    title=item["title"],
                    url=item["url"],
                    resource_type=item["resource_type"],
                    description=item["description"],
                    added_by_discord_id="OFFICIAL",
                    added_by_name="Official Curriculum",
                    is_verified=True,
                    upvotes=5,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(db_item)
            await db.commit()

    def get_curated_roadmaps(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve curated roadmaps for DSA, LLD, HLD, Microservices, and Core CS."""
        if category and category.upper() in CURATED_ROADMAPS:
            return {category.upper(): CURATED_ROADMAPS[category.upper()]}
        return CURATED_ROADMAPS

study_service = StudyService()
