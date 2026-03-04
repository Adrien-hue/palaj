from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.api.deps_authorization import require_admin
from backend.app.api.http_exceptions import bad_request, conflict, forbidden, not_found
from backend.app.dto.users import UserCreate, UserOut, UserUpdate
from backend.app.security.password import hash_password
from db.models import User

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


def _normalize_username(username: str) -> str:
    normalized = username.strip().lower()
    if not normalized:
        bad_request("Invalid payload")
    return normalized


def _normalize_password(password: str) -> str:
    normalized = password.strip()
    if not normalized:
        bad_request("Invalid payload")
    return normalized


def _active_admin_count(db: Session) -> int:
    return (
        db.query(func.count(User.id))
        .filter(User.role == "admin", User.is_active.is_(True))
        .scalar()
        or 0
    )


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(
        username=_normalize_username(payload.username),
        password_hash=hash_password(_normalize_password(payload.password)),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        conflict("Conflict")
    db.refresh(user)
    return user


@router.get("", response_model=list[UserOut])
def list_users(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[User]:
    query = db.query(User)
    if not include_inactive:
        query = query.filter(User.is_active.is_(True))
    return query.order_by(User.id.asc()).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        not_found("Not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        not_found("Not found")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        bad_request("Invalid payload")

    if user.id == actor.id and (
        changes.get("role") == "manager" or changes.get("is_active") is False
    ):
        forbidden("Forbidden")

    was_last_active_admin = (
        user.role == "admin" and user.is_active and _active_admin_count(db) <= 1
    )
    if was_last_active_admin and (
        changes.get("role") == "manager" or changes.get("is_active") is False
    ):
        forbidden("Forbidden")

    if "username" in changes:
        user.username = _normalize_username(changes["username"])
    if "role" in changes:
        user.role = changes["role"]
    if "is_active" in changes:
        user.is_active = changes["is_active"]
    if "password" in changes:
        user.password_hash = hash_password(_normalize_password(changes["password"]))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        conflict("Conflict")

    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
) -> Response:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        not_found("Not found")

    if user.id == actor.id:
        forbidden("Forbidden")

    if user.role == "admin" and user.is_active and _active_admin_count(db) <= 1:
        forbidden("Forbidden")

    user.is_active = False
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        conflict("Conflict")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
