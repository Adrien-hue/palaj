from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from db.models.refresh_token import RefreshToken
from core.application.ports.refresh_token_repo import RefreshTokenRepositoryPort


class SqlAlchemyRefreshTokenRepo(RefreshTokenRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        return self.session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    
    def get_user_id_by_hash(self, token_hash: str) -> Optional[int]:
        rt = (
            self.session.query(RefreshToken.user_id)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
        if not rt:
            return None
        return int(rt[0])

    def add(self, token: RefreshToken) -> None:
        self.session.add(token)

    def revoke(self, token: RefreshToken, now: datetime) -> None:
        token.revoked_at = now

    def revoke_by_hash_if_active(self, token_hash: str, now: datetime) -> bool:
        rt = self.get_by_hash(token_hash)
        if not rt or rt.revoked_at is not None:
            return False
        rt.revoked_at = now
        return True

    def revoke_all_for_user(self, user_id: int, now: datetime) -> int:
        q = self.session.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        count = q.count()
        q.update({"revoked_at": now}, synchronize_session=False)
        return count

    def commit(self) -> None:
        self.session.commit()
