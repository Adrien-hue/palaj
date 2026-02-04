from __future__ import annotations

from datetime import date, time
from pydantic import BaseModel

class TrancheCoverageDTO(BaseModel):
    tranche_id: int
    tranche_nom: str
    heure_debut: time
    heure_fin: time
    required_count: int
    assigned_count: int

class PosteCoverageDayDTO(BaseModel):
    poste_id: int
    day_date: date
    weekday: int  # 0=lundi..6=dimanche
    tranches: list[TrancheCoverageDTO]
