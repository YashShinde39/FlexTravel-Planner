from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from FLEXTRAVEL_* environment variables or backend/.env."""

    model_config = SettingsConfigDict(env_prefix="FLEXTRAVEL_", env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    # Matches docker-compose.yml. Port 5433 avoids clashing with a locally installed Postgres.
    database_url: str = "postgresql+asyncpg://flextravel:flextravel@localhost:5433/flextravel"


@lru_cache
def get_settings() -> Settings:
    return Settings()
