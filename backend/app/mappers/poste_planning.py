from backend.app.dto.poste_planning import (
    PostePlanningResponseDTO,
    PostePlanningDayDTO,
    PostePlanningTrancheDTO,
)

from backend.app.mappers.postes import to_poste_dto
from backend.app.mappers.tranches import to_tranche_dto
from backend.app.mappers.agents_light import to_agent_dto

from core.domain.models.poste_planning import PostePlanning, PostePlanningDay, PostePlanningTranche

def to_poste_tranche_dto(tranche: PostePlanningTranche) -> PostePlanningTrancheDTO:
    return PostePlanningTrancheDTO(
        tranche=to_tranche_dto(tranche.tranche),
        agents=[to_agent_dto(a) for a in tranche.agents],
    )

def to_poste_planning_day_dto(day: PostePlanningDay) -> PostePlanningDayDTO:
    return PostePlanningDayDTO(
        day_date=day.day_date,
        day_type=day.day_type.value if hasattr(day.day_type, "value") else str(day.day_type),
        description=day.description,
        is_off_shift=day.is_off_shift,
        tranches=[to_poste_tranche_dto(t) for t in day.tranches],
    )

def to_poste_planning_response(planning: PostePlanning) -> PostePlanningResponseDTO:
    return PostePlanningResponseDTO(
        poste=to_poste_dto(planning.poste),
        start_date=planning.start_date,
        end_date=planning.end_date,
        days=[to_poste_planning_day_dto(d) for d in planning.days],
    )
