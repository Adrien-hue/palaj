# backend/app/api/mappers/poste_coverage_day.mapper.py
from __future__ import annotations

from backend.app.dto.poste_coverage_day import (
    PosteCoverageDayDTO,
    TrancheCoverageDTO,
)
from core.application.read_models.poste_coverage_day_rm import (
    PosteCoverageDayRM,
    TrancheCoverageRM,
)

def to_tranche_coverage_dto(rm: TrancheCoverageRM) -> TrancheCoverageDTO:
    return TrancheCoverageDTO(
        tranche_id=rm.tranche_id,
        tranche_nom=rm.tranche_nom,
        heure_debut=rm.heure_debut,
        heure_fin=rm.heure_fin,
        required_count=rm.required_count,
        assigned_count=rm.assigned_count,
    )

def to_poste_coverage_day_dto(rm: PosteCoverageDayRM) -> PosteCoverageDayDTO:
    return PosteCoverageDayDTO(
        poste_id=rm.poste_id,
        day_date=rm.day_date,
        weekday=rm.weekday,
        tranches=[to_tranche_coverage_dto(t) for t in rm.tranches],
    )
