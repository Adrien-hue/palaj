from backend.app.dto.planning import AgentPlanningResponseDTO
from backend.app.mappers.agents import to_agent_detail_dto
from backend.app.mappers.planning_day import to_planning_day_dto

def to_agent_planning_response(planning) -> AgentPlanningResponseDTO:
    return AgentPlanningResponseDTO(
        agent=to_agent_detail_dto(planning.agent),
        start_date=planning.start_date,
        end_date=planning.end_date,
        days=[to_planning_day_dto(day) for day in planning.days]
    )