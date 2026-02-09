from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from backend.app.dto.auth import LoginRequest, MeResponse
from backend.app.dto.common.common import ActionResponse 
from backend.app.security.cookies import set_auth_cookies, clear_auth_cookies
from backend.app.settings import settings

from backend.app.api.deps_auth import get_auth_service
from backend.app.api.deps_current_user import current_user
from core.application.services.auth_service import AuthService, AuthError
from db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=ActionResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    auth: AuthService = Depends(get_auth_service),
):
    try:
        pair = auth.login(
            payload.username,
            payload.password,
            user_agent=request.headers.get("user-agent"),
            ip=(request.client.host if request.client else None),
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    set_auth_cookies(response, access_token=pair.access_token, refresh_token=pair.refresh_token)
    return ActionResponse()


@router.post("/refresh", response_model=ActionResponse)
def refresh(
    request: Request,
    response: Response,
    auth: AuthService = Depends(get_auth_service),
):
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        pair = auth.refresh(
            refresh_token,
            user_agent=request.headers.get("user-agent"),
            ip=(request.client.host if request.client else None),
        )
    except AuthError as e:
        clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    set_auth_cookies(response, access_token=pair.access_token, refresh_token=pair.refresh_token)
    return ActionResponse()


@router.post("/logout", response_model=ActionResponse)
def logout(
    request: Request,
    response: Response,
    auth: AuthService = Depends(get_auth_service),
):
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if refresh_token:
        auth.logout(refresh_token)

    clear_auth_cookies(response)
    return ActionResponse()


@router.post("/logout-all", response_model=ActionResponse)
def logout_all(
    request: Request,
    response: Response,
    user: User = Depends(current_user),
    auth: AuthService = Depends(get_auth_service),
):
    auth.logout_all(user.id)
    clear_auth_cookies(response)
    return ActionResponse()


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(current_user)) -> MeResponse:
    return MeResponse(id=user.id, username=user.username, role=user.role, is_active=user.is_active)
