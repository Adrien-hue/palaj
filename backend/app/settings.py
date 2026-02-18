from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/
BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=BASE_DIR / ".env",  # backend/.env
        extra="ignore",
    )

    # ==========================================================
    # ENVIRONMENT
    # ==========================================================
    env: Literal["local", "staging", "production"] = "local"
    debug: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"

    # ==========================================================
    # APP
    # ==========================================================
    app_name: str = "PALAJ API"
    api_prefix: str = "/api"
    api_v1_prefix: str = "/v1"

    # ==========================================================
    # DATABASE
    # ==========================================================
    database_url: str = "sqlite:///./data/palaj.db"

    # ==========================================================
    # JWT (Access Token)
    # ==========================================================
    jwt_secret: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "palaj-api"
    jwt_audience: str = "palaj-web"
    access_token_minutes: int = 15

    # ==========================================================
    # REFRESH TOKEN
    # ==========================================================
    refresh_token_days: int = 30
    refresh_token_pepper: str = "CHANGE_ME_TOO"

    # ==========================================================
    # COOKIES
    # ==========================================================
    access_cookie_name: str = "palaj_at"
    refresh_cookie_name: str = "palaj_rt"

    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: Optional[str] = None

    # ==========================================================
    # CSRF (recommandé si SameSite=None)
    # ==========================================================
    csrf_cookie_name: str = "palaj_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    csrf_enabled: bool = False

    # ==========================================================
    # CORS
    # ==========================================================
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

    # ==========================================================
    # AUTO-ADJUSTMENTS
    # ==========================================================
    def apply_env_defaults(self) -> "Settings":
        """
        Ajustements automatiques selon l'environnement.
        """
        if self.env in ("staging", "production"):
            self.debug = False

            if self.log_level == "DEBUG":
                self.log_level = "INFO"

            # En prod/staging on force HTTPS cookies
            self.cookie_secure = True

        # Si SameSite=None → secure obligatoire (navigateurs modernes)
        if self.cookie_samesite == "none":
            self.cookie_secure = True
            self.csrf_enabled = True

        return self

    def validate_production_safety(self) -> None:
        """
        Empêche le démarrage en production si configuration dangereuse.
        """
        if self.env != "production":
            return

        if self.jwt_secret in ("CHANGE_ME", "", None):
            raise RuntimeError("APP_JWT_SECRET must be set in production.")

        if self.refresh_token_pepper in ("CHANGE_ME_TOO", "", None):
            raise RuntimeError("APP_REFRESH_TOKEN_PEPPER must be set in production.")

        if not self.cors_origins:
            raise RuntimeError("APP_CORS_ORIGINS must be set in production.")

        if self.database_url.startswith("sqlite"):
            raise RuntimeError("SQLite is not allowed in production.")


# Instance globale
settings = Settings().apply_env_defaults()
settings.validate_production_safety()
