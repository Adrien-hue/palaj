# core/application/read_models/poste_coverage_day_rm.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, time

@dataclass(frozen=True)
class PosteCoverageDayRM:
    poste_id: int
    day_date: date
    weekday: int  # 0=lundi..6=dimanche
    tranches: list[TrancheCoverageRM]

@dataclass(frozen=True)
class TrancheCoverageRM:
    tranche_id: int
    tranche_nom: str
    heure_debut: time
    heure_fin: time
    required_count: int
    assigned_count: int
