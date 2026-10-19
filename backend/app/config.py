"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the AppReviewr API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APPREVIEW_",
        extra="ignore",
    )

    app_name: str = "AppReviewr"
    environment: str = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8741
    cors_origins: str = "http://localhost:3741,http://127.0.0.1:3741"

    # Cache / storage
    database_url: str = "sqlite+aiosqlite:///./data/appreviewr.db"
    cache_ttl_hours: int = 12

    # Job / rate limits
    max_reviews_per_job: int = 2000
    max_countries_per_job: int = 10
    rate_limit_per_ip: str = "30/minute"
    job_rate_limit_per_ip: str = "10/hour"

    # Scraper
    http_timeout_seconds: float = 30.0
    http_max_retries: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
