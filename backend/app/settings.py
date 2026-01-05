from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PALAJ API"
    api_prefix: str = "/api"
    api_v1_prefix: str = "/v1"
    debug: bool = True

    database_url: str = "sqlite:///./data/palaj.db"

    jwt_secret: str = "CHANGE_ME"
    jwt_expires_minutes: int = 60 * 8

    auth_cookie_name: str = "access_token"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    auth_cookie_domain: str | None = None

    # CORS
    cors_origins: str = ""

    FEATURE_AGENT_DAY_READ_DB: bool = True

    class Config:
        env_prefix = "APP_"
        env_file = ".env"


settings = Settings()
