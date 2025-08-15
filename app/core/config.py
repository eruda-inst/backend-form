from pydantic_settings import BaseSettings
from pydantic import AnyUrl
from typing import Optional, Tuple
import os

class Settings(BaseSettings):
    MEDIA_ROOT: str = "media"
    MEDIA_URL: str = "/media"
    MAX_IMAGE_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: Tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")
    BASE_URL: Optional[AnyUrl] = None

    def ensure_media_dir(self) -> None:
        os.makedirs(self.MEDIA_ROOT, exist_ok=True)

settings = Settings()
settings.ensure_media_dir()
