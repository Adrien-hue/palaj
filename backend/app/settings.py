from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Planning Assistant API"
    api_prefix: str = "/api"
    api_v1_prefix: str = "/v1"
    debug: bool = True


settings = Settings()
