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
    # Sonnet 4.6 for the tool-use research loop — Opus 4.7 was costing
    # ~$2/run because Opus pricing × growing tool_result history × up to
    # 8 iterations. Sonnet 4.6 cuts inference cost to ~60% (Opus 4.7 is
    # $5/$25 per 1M; Sonnet 4.6 is $3/$15) and handles the short-horizon
    # tool-picking task well. Pair with prompt caching in tools.py for
    # the rest of the savings.
    research_model: str = "claude-sonnet-4-6"
    planner_max_tokens: int = 1024
    designer_max_tokens: int = 2048
    research_max_tokens: int = 4096
    research_max_iterations: int = 8

    mcp_electronics_path: str | None = None
    mcp_cad_path: str | None = None
    mcp_mechanical_path: str | None = None
    mcp_fluids_path: str | None = None
    cad_base_url: str = "http://127.0.0.1:8002"
    cad_shared_secret: str | None = None
    uv_command: str = "uv"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
