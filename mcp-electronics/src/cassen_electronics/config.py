from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    nexar_client_id: str | None = None
    nexar_client_secret: str | None = None

    mouser_api_key: str | None = None

    digikey_client_id: str | None = None
    digikey_client_secret: str | None = None

    search_cache_ttl_s: int = 300
    part_cache_ttl_s: int = 1800
    request_timeout_s: float = 15.0
    default_limit: int = 10

    @property
    def nexar_configured(self) -> bool:
        return bool(self.nexar_client_id and self.nexar_client_secret)

    @property
    def mouser_configured(self) -> bool:
        return bool(self.mouser_api_key)

    @property
    def digikey_configured(self) -> bool:
        return bool(self.digikey_client_id and self.digikey_client_secret)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
