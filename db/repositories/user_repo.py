from __future__ import annotations
from sqlalchemy.orm import Session
from typing import Optional
from db.models import User
from core.application.ports.user_repo import UserRepositoryPort

class SqlAlchemyUserRepo(UserRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == user_id).first()
