import logging
import base64
from pathlib import Path
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings
from database.models import UserProfile

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False

class ProfileService:
    def __init__(self):
        self._fernet = None
        if _FERNET_AVAILABLE:
            try:
                self._fernet = Fernet(settings.DATA_ENCRYPTION_KEY.encode())
            except Exception:
                key = Fernet.generate_key()
                self._fernet = Fernet(key)

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive string data."""
        if not data:
            return ""
        if self._fernet:
            return self._fernet.encrypt(data.encode()).decode()
        # Fallback basic obfuscation if cryptography lib not yet installed
        return "b64:" + base64.b64encode(data.encode()).decode()

    def decrypt_data(self, token: str) -> str:
        """Decrypt sensitive encrypted token."""
        if not token:
            return ""
        try:
            if token.startswith("b64:"):
                return base64.b64decode(token[4:].encode()).decode()
            if self._fernet:
                return self._fernet.decrypt(token.encode()).decode()
            return token
        except Exception as e:
            logger.error(f"Error decrypting token: {e}")
            return ""

    async def get_profile(self, db: AsyncSession, discord_id: str) -> Optional[UserProfile]:
        """Fetch a user profile by Discord ID."""
        result = await db.execute(select(UserProfile).where(UserProfile.discord_id == str(discord_id)))
        return result.scalars().first()

    async def get_or_create_profile(self, db: AsyncSession, discord_id: str, username: str) -> UserProfile:
        """Fetch or create a new user profile."""
        profile = await self.get_profile(db, str(discord_id))
        if not profile:
            profile = UserProfile(discord_id=str(discord_id), username=username)
            db.add(profile)
            await db.flush()
        return profile

    async def update_profile(
        self,
        db: AsyncSession,
        discord_id: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        current_role: Optional[str] = None,
        current_company: Optional[str] = None,
        years_of_experience: Optional[int] = None,
        notice_period_days: Optional[int] = None,
        requires_sponsorship: Optional[bool] = None,
        target_companies: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """Update fields for a user profile."""
        profile = await self.get_or_create_profile(db, discord_id, username or "User")

        if full_name is not None:
            profile.full_name = full_name
        if current_role is not None:
            profile.current_role = current_role
        if current_company is not None:
            profile.current_company = current_company
        if years_of_experience is not None:
            profile.years_of_experience = years_of_experience
        if notice_period_days is not None:
            profile.notice_period_days = notice_period_days
        if requires_sponsorship is not None:
            profile.requires_sponsorship = requires_sponsorship
        if target_companies is not None:
            profile.target_companies = target_companies

        for k, v in kwargs.items():
            if hasattr(profile, k) and v is not None:
                setattr(profile, k, v)

        return profile

    async def set_target_companies(
        self,
        db: AsyncSession,
        discord_id: str,
        companies: str,
        username: str = "User"
    ) -> UserProfile:
        """Set user's target companies list."""
        profile = await self.get_or_create_profile(db, discord_id, username)
        profile.target_companies = companies.strip()
        await db.flush()
        return profile

    async def save_resume_file(
        self,
        db: AsyncSession,
        discord_id: str,
        filename: str,
        file_bytes: bytes,
        username: str = "User"
    ) -> str:
        """Save user's uploaded resume to disk and record path in database."""
        profile = await self.get_or_create_profile(db, discord_id, username)
        
        user_dir = settings.RESUME_STORAGE_DIR / str(discord_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        safe_filename = Path(filename).name
        target_path = user_dir / safe_filename
        
        with open(target_path, "wb") as f:
            f.write(file_bytes)
            
        profile.resume_file_path = str(target_path)
        profile.resume_filename = safe_filename
        return str(target_path)

    async def save_linkedin_cookie(
        self,
        db: AsyncSession,
        discord_id: str,
        li_at_cookie: str,
        username: str = "User"
    ) -> None:
        """Securely encrypt and store user's LinkedIn session cookie."""
        profile = await self.get_or_create_profile(db, discord_id, username)
        profile.linkedin_cookie_enc = self.encrypt_data(li_at_cookie)

    def get_decrypted_linkedin_cookie(self, profile: UserProfile) -> Optional[str]:
        """Retrieve and decrypt LinkedIn session cookie."""
        if not profile.linkedin_cookie_enc:
            return None
        return self.decrypt_data(profile.linkedin_cookie_enc)

profile_service = ProfileService()
