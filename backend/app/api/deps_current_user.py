from fastapi import Depends, HTTPException, Request, status

from backend.app.settings import settings
from backend.app.api.deps_auth import get_user_auth_service
from core.application.services.user_auth_service import UserAuthService, UserAuthError
from db.models import User


def current_user(
    request: Request,
    user_auth: UserAuthService = Depends(get_user_auth_service),
) -> User:
    token = request.cookies.get(settings.access_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        return user_auth.get_current_user(token)
    except UserAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
