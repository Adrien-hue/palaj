from typing import List, Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )

    # App
    app_name: str = "PALAJ API"
    api_prefix: str = "/api"
    api_v1_prefix: str = "/v1"
    debug: bool = True

    # DB
    database_url: str = "sqlite:///./data/palaj.db"

    # JWT (access token)
    jwt_secret: str = "CHANGE_ME"  # mettre un vrai secret en prod
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "palaj-api"
    jwt_audience: str = "palaj-web"
    access_token_minutes: int = 15  # court

    # Refresh token
    refresh_token_days: int = 30
    refresh_token_pepper: str = "CHANGE_ME_TOO"  # secret supplémentaire pour hasher les refresh tokens

    # Cookies
    access_cookie_name: str = "palaj_at"
    refresh_cookie_name: str = "palaj_rt"
    cookie_secure: bool = False  # True en prod (HTTPS)
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: Optional[str] = None

    # CSRF (à utiliser si cookie_samesite == "none")
    csrf_cookie_name: str = "palaj_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    csrf_enabled: bool = False

    # CORS
    cors_origins: List[str] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("[") and s.endswith("]"):
                import json
                return json.loads(s)
            return [item.strip() for item in s.split(",") if item.strip()]
        return []

settings = Settings()
