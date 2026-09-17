import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

def load_env_file():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = val.strip().strip("'\"")

load_env_file()

@dataclass
class StudyTrackerSettings:
    # Discord Configuration
    DISCORD_BOT_TOKEN: str = os.getenv("STUDY_BOT_TOKEN", os.getenv("DISCORD_BOT_TOKEN", ""))
    DISCORD_GUILD_ID: Optional[str] = os.getenv("DISCORD_GUILD_ID", None)

    # Gemini AI Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

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
