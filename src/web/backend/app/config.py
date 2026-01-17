from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Project Bootstrap"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database (SQLite for local dev, PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./bootstrap.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30

    # Claude API
    anthropic_api_key: Optional[str] = None

    # Integrations
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    gitlab_client_id: Optional[str] = None
    gitlab_client_secret: Optional[str] = None
    jira_base_url: Optional[str] = None

    # CORS (include various dev ports)
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
    ]

def get_settings() -> Settings:
    """Get settings - no cache for development hot-reload."""
    return Settings()
