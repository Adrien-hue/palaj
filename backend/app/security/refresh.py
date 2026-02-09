import hashlib, secrets
from datetime import datetime, timedelta, timezone
from backend.app.settings import settings

def generate_refresh_token() -> str:
    # 256 bits
    return secrets.token_urlsafe(32)

def hash_refresh_token(token: str) -> str:
    # pepper secret en env (jamais en DB)
    raw = (token + settings.refresh_token_pepper).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def refresh_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
