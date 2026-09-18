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

def _generate_default_key() -> str:
    if _HAS_FERNET:
        return Fernet.generate_key().decode()
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

@dataclass
class Settings:
    # Discord Configuration
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_GUILD_ID: Optional[str] = os.getenv("DISCORD_GUILD_ID", None)

    # Gemini & Google Cloud Vertex AI Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("VERTEX_API_KEY") or os.getenv("GOOGLE_API_KEY") or None
    VERTEX_API_KEY: Optional[str] = os.getenv("VERTEX_API_KEY") or None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or None
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "seraphic-rune-366616"
    GCP_LOCATION: str = os.getenv("GCP_LOCATION") or os.getenv("VERTEX_LOCATION") or "us-central1"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER") or "auto"  # "auto", "gemini", "vertex", "openrouter"



    # OpenRouter Integration
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY", None)
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip('/')
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "https://discord-job-bot.local")
    OPENROUTER_APP_NAME: str = os.getenv("OPENROUTER_APP_NAME", "Discord Job Bot")

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
