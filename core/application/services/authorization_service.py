from __future__ import annotations
from db.models import User


class AuthorizationError(Exception):
    pass


class AuthorizationService:
    def require_role(self, user: User, role: str) -> None:
        if user.role != role:
            raise AuthorizationError(f"Role '{role}' required")
