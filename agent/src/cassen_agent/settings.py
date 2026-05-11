"""Process-wide config. Read from .env via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---------------------------------------------------------
    anthropic_api_key: str
    planner_model: str = "claude-sonnet-4-6"
    research_model: str = "claude-haiku-4-5"
    planner_max_tokens: int = 1024
    research_max_tokens: int = 4096

    # --- Supabase ----------------------------------------------------
    supabase_url: str
    supabase_service_role_key: str

    # --- Service surface --------------------------------------------
    # Bearer-token gate matching app/'s AGENT_SHARED_SECRET. When
    # empty (dev only), server warns at startup and accepts any auth.
    agent_shared_secret: str = ""
    agent_host: str = "127.0.0.1"
    agent_port: int = 8001


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
