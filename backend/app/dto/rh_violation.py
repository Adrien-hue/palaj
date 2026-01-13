from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Dict, Any, Literal

from pydantic import BaseModel

SeverityDTO = Literal["info", "warning", "error"]


class RhViolationDTO(BaseModel):
    """
    Violation RH exposée à l'API.

    Stable, explicite, orientée affichage + debug.
    """

    code: str
    rule: str
    severity: SeverityDTO
    message: str

    # Périmètre concerné
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    # Données techniques / explicatives (non affichées directement)
    meta: Dict[str, Any] = {}
