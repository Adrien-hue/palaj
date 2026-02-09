from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from core.application.services.auth_service import AuthService
from core.application.services.user_auth_service import UserAuthService
from db.repositories.user_repo import SqlAlchemyUserRepo
from db.repositories.refresh_token_repo import SqlAlchemyRefreshTokenRepo


def get_auth_service(session: Session = Depends(get_db)) -> AuthService:
    return AuthService(
        users=SqlAlchemyUserRepo(session),
        refresh_tokens=SqlAlchemyRefreshTokenRepo(session),
    )


def get_user_auth_service(session: Session = Depends(get_db)) -> UserAuthService:
    return UserAuthService(users=SqlAlchemyUserRepo(session))
