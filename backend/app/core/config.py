import os
import tempfile

from pydantic_settings import BaseSettings


def _default_download_dir() -> str:
    return os.path.join(tempfile.gettempdir(), "saveany-downloads")


class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_MONTHLY_PRICE_ID: str = ""
    STRIPE_PRO_YEARLY_PRICE_ID: str = ""

    OPENAI_API_KEY: str = ""

    DATABASE_URL: str = "sqlite+aiosqlite:///./saveany.db"

    DOWNLOAD_DIR: str = _default_download_dir()
    MAX_CONCURRENT_DOWNLOADS: int = 5
    TEMP_FILE_EXPIRY_MINUTES: int = 30
    FREE_DAILY_LIMIT: int = 3
    FREE_MAX_RESOLUTION: int = 720
    LARGE_FILE_THRESHOLD: int = 500 * 1024 * 1024  # 500MB

    # Pricing display (shown to users; keep in sync with Stripe dashboard)
    PRO_MONTHLY_PRICE_DISPLAY: str = "$9.9"
    PRO_YEARLY_PRICE_DISPLAY: str = "$99"
    PRO_YEARLY_SAVINGS_DISPLAY: str = "Save 17%"

    # Site metadata
    SITE_NAME: str = "SaveAny"

    class Config:
        env_file = ".env"


settings = Settings()
