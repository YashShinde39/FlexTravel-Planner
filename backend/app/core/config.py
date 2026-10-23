from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from FLEXTRAVEL_* environment variables or backend/.env."""

    model_config = SettingsConfigDict(env_prefix="FLEXTRAVEL_", env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    # Matches docker-compose.yml. Port 5433 avoids clashing with a locally installed Postgres.
    database_url: str = "postgresql+asyncpg://flextravel:flextravel@localhost:5433/flextravel"
    # OpenTripPlanner, the interim routing engine (ADR-0014). Matches docker-compose.yml.
    otp_url: str = "http://localhost:8080"
    # Photon: OpenStreetMap search built for type-ahead (Nominatim forbids autocomplete).
    # Empty disables landmark and address suggestions; stops and stations still work.
    photon_url: str = "https://photon.komoot.io"


@lru_cache
def get_settings() -> Settings:
    return Settings()
