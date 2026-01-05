# backend/app/mappers/planning_day_mapper.py
from backend.app.dto.planning_day import PlanningDayDTO
from backend.app.dto.tranches import TrancheDTO
from core.domain.models.planning_day import PlanningDay

def to_planning_day_dto(day: PlanningDay) -> PlanningDayDTO:
    return PlanningDayDTO(
        day_date=day.day_date,
        day_type=day.day_type,
        description=day.description,
        is_off_shift=day.is_off_shift,
        tranches=[
            TrancheDTO(
                id=t.id,
                nom=t.nom,
                heure_debut=t.heure_debut,
                heure_fin=t.heure_fin,
                poste_id=t.poste_id,
            )
            for t in day.tranches
        ],
    )
