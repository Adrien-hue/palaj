from __future__ import annotations

from backend.app.security.jwt import decode_access_token
from core.application.ports.user_repo import UserRepositoryPort
from db.models import User


class UserAuthError(Exception):
    pass


class UserAuthService:
    def __init__(self, users: UserRepositoryPort):
        self.users = users

    def get_current_user(self, access_token: str) -> User:
        try:
            payload = decode_access_token(access_token)
        except ValueError:
            raise UserAuthError("Invalid token")

        sub = payload.get("sub")
        if not sub or not str(sub).isdigit():
            raise UserAuthError("Invalid token payload")

        user = self.users.get_by_id(int(sub))
        if not user or not user.is_active:
            raise UserAuthError("User not found or inactive")

        return user
