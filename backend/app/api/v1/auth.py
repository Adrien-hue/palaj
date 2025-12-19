from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db, current_user
from backend.app.security.password import verify_password
from backend.app.security.jwt import create_access_token
from backend.app.settings import settings

from db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class MeResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

@router.post("/login")
def login(payload: LoginRequest, response: Response, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    token = create_access_token(sub=user.username, role=user.role)

    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        domain=settings.auth_cookie_domain,
        path="/",
        max_age=settings.jwt_expires_minutes * 60,
    )
    return {"status": "ok"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.auth_cookie_name, path="/", domain=settings.auth_cookie_domain)
    return {"status": "ok"}

@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(current_user)) -> MeResponse:
    return MeResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
    )