from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AppError(Exception):
    code: str
    details: Optional[dict[str, Any]] = None


class NotFoundError(AppError): ...
class ConflictError(AppError): ...
class ValidationError(AppError): ...
