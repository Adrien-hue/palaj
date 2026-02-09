from __future__ import annotations
from typing import Optional, Protocol, runtime_checkable
from db.models import User

@runtime_checkable
class UserRepositoryPort(Protocol):
    def get_by_username(self, username: str) -> Optional[User]: ...
    def get_by_id(self, user_id: int) -> Optional[User]: ...