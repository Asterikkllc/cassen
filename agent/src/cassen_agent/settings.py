from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str

    supabase_url: str
    supabase_service_role_key: str

    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    agent_shared_secret: str
    agent_host: str = "127.0.0.1"
    agent_port: int = 8001

    primary_model: str = "claude-sonnet-4-6"
    planner_max_tokens: int = 1024
    designer_max_tokens: int = 2048


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
