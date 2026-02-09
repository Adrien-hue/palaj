from fastapi import Depends, HTTPException, status

from backend.app.api.deps_current_user import current_user
from core.application.services.authorization_service import AuthorizationService, AuthorizationError
from db.models import User


def require_role(role: str):
    def _require(user: User = Depends(current_user)) -> User:
        try:
            AuthorizationService().require_role(user, role)
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        return user

    return _require