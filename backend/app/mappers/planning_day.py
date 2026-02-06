# backend/app/mappers/planning_day_mapper.py
from backend.app.dto.planning_day import AgentPlanningDayDTO, PlanningDayDTO
from backend.app.mappers.tranches import to_tranche_dto
from core.domain.models.planning_day import PlanningDay

def to_planning_day_dto(day: PlanningDay) -> PlanningDayDTO:
    return PlanningDayDTO(
        day_date=day.day_date,
        day_type=day.day_type,
        description=day.description,
        is_off_shift=day.is_off_shift,
        tranches=[
            to_tranche_dto(t) for t in day.tranches
        ],
    )

def to_agent_planning_day_dto(agent_id: int, day: PlanningDay) -> AgentPlanningDayDTO:
    return AgentPlanningDayDTO(
        agent_id=agent_id,
        planning_day=to_planning_day_dto(day),
    )