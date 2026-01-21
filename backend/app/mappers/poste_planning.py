from backend.app.dto.poste_planning import (
    PostePlanningResponseDTO,
    PostePlanningDayDTO,
    PostePlanningTrancheDTO,
)

from backend.app.mappers.postes import to_poste_dto
from backend.app.mappers.tranches import to_tranche_dto
from backend.app.mappers.agents_light import to_agent_dto

from core.domain.models.poste_planning import PostePlanning


def to_poste_planning_response(planning: PostePlanning) -> PostePlanningResponseDTO:
    return PostePlanningResponseDTO(
        poste=to_poste_dto(planning.poste),
        start_date=planning.start_date,
        end_date=planning.end_date,
        days=[
            PostePlanningDayDTO(
                day_date=d.day_date,
                day_type=d.day_type.value if hasattr(d.day_type, "value") else str(d.day_type),
                description=d.description,
                is_off_shift=d.is_off_shift,
                tranches=[
                    PostePlanningTrancheDTO(
                        tranche=to_tranche_dto(pt.tranche),
                        agents=[to_agent_dto(a) for a in pt.agents],
                    )
                    for pt in d.tranches
                ],
            )
            for d in planning.days
        ],
    )
