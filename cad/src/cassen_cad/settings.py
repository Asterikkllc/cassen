from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    cad_shared_secret: str
    cad_host: str = "127.0.0.1"
    cad_port: int = 8002
    max_step_bytes: int = 50 * 1024 * 1024

    # Hyper3D Rodin Gen-2 (PRD section 5.2 tier 3 — generative geometry)
    hyper3d_api_key: str | None = None
    hyper3d_base_url: str = "https://hyperhuman.deemos.com/api/v2"
    hyper3d_poll_interval_s: float = 4.0
    hyper3d_max_wait_s: float = 600.0  # 10 min ceiling for any single job
    max_rodin_output_bytes: int = 50 * 1024 * 1024


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
