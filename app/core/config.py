"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "SEO Maximus Backend"
    environment: str = "development"
    debug: bool = True

    api_v1_prefix: str = "/v1"
    cors_allowed_origins: List[str] = ["*"]

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/seo_maximus"
    redis_url: str = "redis://localhost:6379/0"

    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    tinypng_api_key: Optional[str] = None
    image_storage_bucket: Optional[str] = None
    storage_public_base_url: Optional[str] = None

    playwright_timeout_seconds: int = 60
    playwright_viewports: List[str] = ["desktop", "mobile"]

    auth_jwt_secret: str = "change-me"
    auth_jwt_algorithm: str = "HS256"
    auth_token_header: str = "Authorization"

    sentry_dsn: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()

