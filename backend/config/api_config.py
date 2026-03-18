"""Application settings — loaded from environment / .env file."""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.config.paths import PROJECT_ROOT


class Config(BaseSettings):
    """Centralised config. Values come from env vars / .env file."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Backend"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    log_level: str = "INFO"

    github_username: str = "0xd3ny5"
    github_token: str = ""

    admin_username: str = "admin"
    admin_password: str = "admin"

    allowed_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    allowed_hosts: list[str] = []

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/me"
    echo: bool = False

    @model_validator(mode="after")
    def _warn_insecure_defaults(self) -> Config:
        if not self.debug and self.secret_key == "change-me-in-production":
            logging.getLogger(__name__).warning(
                "SECRET_KEY is still the default! Set a strong key for production."
            )
        if not self.debug and self.admin_password == "admin":
            logging.getLogger(__name__).warning(
                "ADMIN_PASSWORD is still the default! Change it for production."
            )
        return self


@lru_cache
def get_config() -> Config:
    """Singleton settings instance, cached after first call."""
    return Config()
