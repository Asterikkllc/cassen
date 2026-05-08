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
    # Haiku 4.5 for the tool-use research loop. Three reasons:
    # (1) Highest tier-1 ITPM headroom of the three models — 50K
    #     vs Sonnet's 30K vs Opus's 500K. With ~30-40K fresh
    #     input tokens per multi-domain run, Sonnet 4.6 is right
    #     at the cap and prone to 429s; Haiku has comfortable
    #     headroom; Opus is overkill on rate but expensive.
    # (2) Cheapest by ~3x ($1/$5 per 1M vs Sonnet's $3/$15) —
    #     research nodes are pure tool-picking against a curated
    #     catalog or live distributor, which is Haiku's wheelhouse.
    # (3) Cache reads are excluded from ITPM accounting (per
    #     console rate-limit page), so the prompt caching in
    #     tools.py compounds the headroom — only fresh tokens
    #     count. Haiku's 50K + caching = comfortable margin.
    research_model: str = "claude-haiku-4-5"
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
