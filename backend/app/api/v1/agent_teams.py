from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_agent_team_service, require_role
from backend.app.dto.agent_team import AgentTeamsUpdateDTO
from backend.app.dto.team import TeamDTO
from core.application.services.teams.agent_team_service import AgentTeamService
from core.application.services.teams.exceptions import NotFoundError

router = APIRouter(prefix="/agents", tags=["agent-teams"])


@router.get("/{agent_id}/teams", response_model=List[TeamDTO])
def list_agent_teams(
    agent_id: int,
    service: AgentTeamService = Depends(get_agent_team_service),
):
    try:
        return service.list_teams_for_agent(agent_id)
    except NotFoundError as e:
        # agent_not_found
        raise HTTPException(status_code=404, detail=e.code)


@router.put("/{agent_id}/teams", status_code=status.HTTP_204_NO_CONTENT)
def set_agent_teams(
    agent_id: int,
    payload: AgentTeamsUpdateDTO,
    service: AgentTeamService = Depends(get_agent_team_service),
):
    try:
        service.set_agent_teams(agent_id, payload.team_ids)
        return None
    except NotFoundError as e:
        # agent_not_found OU team_not_found (avec missing_team_ids)
        if e.details:
            raise HTTPException(status_code=404, detail={"code": e.code, **e.details})
        raise HTTPException(status_code=404, detail=e.code)
