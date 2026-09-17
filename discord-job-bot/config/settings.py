import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import secrets
import base64

try:
    from cryptography.fernet import Fernet
    _HAS_FERNET = True
except ImportError:
    _HAS_FERNET = False

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env manually if python-dotenv is not installed
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

def _generate_default_key() -> str:
    if _HAS_FERNET:
        return Fernet.generate_key().decode()
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

@dataclass
class Settings:
    # Discord Configuration
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_GUILD_ID: Optional[str] = os.getenv("DISCORD_GUILD_ID", None)

    # AI Model Configuration (APIENX Integration & Google Gemini)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    APIENX_API_KEY: Optional[str] = os.getenv("APIENX_API_KEY", os.getenv("GEMINI_API_KEY", None))
    APIENX_BASE_URL: str = os.getenv("APIENX_BASE_URL", os.getenv("AI_BASE_URL", "https://api.apienx.com/v1"))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "free/gemini-3.8-flash")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "apienx")

    # API Keys for Jobs
    RAPIDAPI_KEY: Optional[str] = os.getenv("RAPIDAPI_KEY", None)
    ADZUNA_APP_ID: Optional[str] = os.getenv("ADZUNA_APP_ID", None)
    ADZUNA_APP_KEY: Optional[str] = os.getenv("ADZUNA_APP_KEY", None)

    # Security & Encryption
    DATA_ENCRYPTION_KEY: str = os.getenv("DATA_ENCRYPTION_KEY", _generate_default_key())

    # Database & Storage
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{BASE_DIR.as_posix()}/data/bot.db"
    )
    DATA_DIR: Path = BASE_DIR / "data"
    RESUME_STORAGE_DIR: Path = BASE_DIR / "data" / "resumes"
    SCREENSHOT_STORAGE_DIR: Path = BASE_DIR / "data" / "screenshots"

    # Automation Engine
    HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "true").lower() in ("true", "1", "yes")
    BROWSER_TIMEOUT_MS: int = int(os.getenv("BROWSER_TIMEOUT_MS", "45000"))
    MAX_CONCURRENT_APPLICATIONS: int = int(os.getenv("MAX_CONCURRENT_APPLICATIONS", "3"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

def get_settings() -> Settings:
    settings_obj = Settings()
    settings_obj.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings_obj.RESUME_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings_obj.SCREENSHOT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return settings_obj

settings = get_settings()
