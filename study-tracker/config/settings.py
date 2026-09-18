import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

def load_env_file():
    for env_path in [BASE_DIR / ".env", BASE_DIR.parent / ".env"]:
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, val = line.partition("=")
                        k = key.strip()
                        v = val.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v

load_env_file()

# Resolve relative GOOGLE_APPLICATION_CREDENTIALS if specified
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    cred_path = Path(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    if not cred_path.is_absolute():
        for candidate in [BASE_DIR / cred_path, BASE_DIR.parent / cred_path]:
            if candidate.exists():
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(candidate.resolve())
                break

@dataclass
class StudyTrackerSettings:
    # Discord Configuration
    DISCORD_BOT_TOKEN: str = os.getenv("STUDY_BOT_TOKEN", os.getenv("DISCORD_BOT_TOKEN", ""))
    DISCORD_GUILD_ID: Optional[str] = os.getenv("DISCORD_GUILD_ID", None)

    # Gemini & Google Cloud Vertex AI Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("VERTEX_API_KEY") or os.getenv("GOOGLE_API_KEY") or None
    VERTEX_API_KEY: Optional[str] = os.getenv("VERTEX_API_KEY") or None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or None
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "seraphic-rune-366616"
    GCP_LOCATION: str = os.getenv("GCP_LOCATION") or os.getenv("VERTEX_LOCATION") or "us-central1"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER") or "auto"



    # OpenRouter Integration
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY", None)
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip('/')
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash-vl:free")
    OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "https://discord-job-bot.local")
    OPENROUTER_APP_NAME: str = os.getenv("OPENROUTER_APP_NAME", "Study Tracker Coach Bot")

    # Database & Storage
    DATABASE_URL: str = os.getenv(
        "STUDY_DATABASE_URL",
        f"sqlite+aiosqlite:///{BASE_DIR.as_posix()}/data/study_tracker.db"
    )
    DATA_DIR: Path = BASE_DIR / "data"

    # Defaults
    DEFAULT_POMODORO_MINUTES: int = 25
    DEFAULT_DAILY_GOAL_MINUTES: int = 120
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

def get_settings() -> StudyTrackerSettings:
    settings_obj = StudyTrackerSettings()
    settings_obj.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return settings_obj

settings = get_settings()
