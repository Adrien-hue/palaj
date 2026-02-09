from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from backend.app.security.jwt import create_access_token, decode_access_token
from backend.app.security.password import verify_password
from backend.app.security.refresh import (
    generate_refresh_token, hash_refresh_token, refresh_expires_at
)
from db.models.refresh_token import RefreshToken
from db.models import User
from core.application.ports.user_repo import UserRepositoryPort
from core.application.ports.refresh_token_repo import RefreshTokenRepositoryPort


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class RefreshResult:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self, users: UserRepositoryPort, refresh_tokens: RefreshTokenRepositoryPort):
        self.users = users
        self.refresh_tokens = refresh_tokens

    def login(self, username: str, password: str, *, user_agent: Optional[str], ip: Optional[str]) -> LoginResult:
        user = self.users.get_by_username(username)
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthError("Bad credentials")

        access = create_access_token(user_id=user.id, role=user.role)
        refresh = generate_refresh_token()

        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=refresh_expires_at(),
            user_agent=user_agent,
            ip=ip,
        )
        self.refresh_tokens.add(rt)
        self.refresh_tokens.commit()

        return LoginResult(access_token=access, refresh_token=refresh)
    
    def logout(self, refresh_token: Optional[str]) -> None:
        if not refresh_token:
            return

        now = datetime.now(timezone.utc)
        token_hash = hash_refresh_token(refresh_token)

        revoked = self.refresh_tokens.revoke_by_hash_if_active(token_hash, now)
        if revoked:
            self.refresh_tokens.commit()

    def logout_all(self, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        count = self.refresh_tokens.revoke_all_for_user(user_id, now)
        self.refresh_tokens.commit()
        return count

    def refresh(self, refresh_token: str, *, user_agent: Optional[str], ip: Optional[str]) -> RefreshResult:
        token_hash = hash_refresh_token(refresh_token)

        rt = self.refresh_tokens.get_by_hash(token_hash)
        if not rt:
            raise AuthError("Invalid refresh token")

        now = datetime.now(timezone.utc)

        # --- REUSE / ABUSE DETECTION ---
        if rt.revoked_at is not None:
            self.refresh_tokens.revoke_all_for_user(rt.user_id, now)
            self.refresh_tokens.commit()
            raise AuthError("Refresh token reuse detected")

        expires_at = rt.expires_at
        if expires_at.tzinfo is None:
            now_cmp = datetime.utcnow()  # naive
        else:
            now_cmp = now

        if rt.expires_at <= now_cmp:
            self.refresh_tokens.revoke_all_for_user(rt.user_id, now)
            self.refresh_tokens.commit()
            raise AuthError("Refresh token expired")

        user = self.users.get_by_id(rt.user_id)
        if not user or not user.is_active:
            self.refresh_tokens.revoke_all_for_user(rt.user_id, now)
            self.refresh_tokens.commit()
            raise AuthError("User inactive")

        self.refresh_tokens.revoke(rt, now)

        new_refresh = generate_refresh_token()
        self.refresh_tokens.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(new_refresh),
                expires_at=refresh_expires_at(),
                user_agent=user_agent,
                ip=ip,
            )
        )

        access = create_access_token(user_id=user.id, role=user.role)
        self.refresh_tokens.commit()

        return RefreshResult(access_token=access, refresh_token=new_refresh)
