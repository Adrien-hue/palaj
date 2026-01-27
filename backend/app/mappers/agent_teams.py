from backend.app.dto.agent_team import AgentTeamDTO
from core.domain.entities.agent_team import AgentTeam


def to_agent_team_dto(x: AgentTeam) -> AgentTeamDTO:
    return AgentTeamDTO(
        agent_id=x.agent_id,
        team_id=x.team_id,
        created_at=x.created_at,
    )
