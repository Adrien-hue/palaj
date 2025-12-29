from backend.app.dto.agents import AgentDTO
from backend.app.dto.planning import AgentPlanningResponseDTO
from backend.app.mappers.work_days import to_work_day_dto

def to_agent_planning_response(planning) -> AgentPlanningResponseDTO:
    agent = planning.agent
    sorted_work_days = sorted(planning.work_days or [], key=lambda wd: wd.jour)

    return AgentPlanningResponseDTO(
        agent=AgentDTO(
            id=agent.id,
            nom=agent.nom,
            prenom=agent.prenom,
            code_personnel=getattr(agent, "code_personnel", None),
        ),
        start_date=planning.start_date,
        end_date=planning.end_date,
        work_days=[to_work_day_dto(wd) for wd in sorted_work_days],
    )