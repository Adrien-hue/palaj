from __future__ import annotations

from typing import Any, NoReturn
from fastapi import HTTPException, status


def bad_request(detail: Any = "Bad request") -> NoReturn:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def unauthorized(detail: Any = "Not authenticated") -> NoReturn:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def forbidden(detail: Any = "Forbidden") -> NoReturn:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def not_found(detail: Any = "Not found") -> NoReturn:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def conflict(detail: Any = "Conflict") -> NoReturn:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def unprocessable_entity(detail: Any = "Unprocessable entity") -> NoReturn:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
