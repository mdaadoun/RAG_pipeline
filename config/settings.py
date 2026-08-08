"""Type-safe application configuration settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    input_dir: str = "./data/input"
    output_dir: str = "./data/output"
    default_chunk_size: int = 512
    default_overlap: int = 64
    min_chunk_size: int = 50
    character_coverage_threshold: float = 0.98


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
