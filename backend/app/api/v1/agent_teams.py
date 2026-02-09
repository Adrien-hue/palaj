from fastapi import APIRouter, Depends, Query, status

from backend.app.api.deps import get_agent_team_service
from backend.app.api.http_exceptions import conflict, not_found
from backend.app.mappers.agent_teams import to_agent_team_dto
from core.application.services.teams.agent_team_service import AgentTeamService
from core.application.services.exceptions import NotFoundError

router = APIRouter(prefix="/agent-teams", tags=["Agent teams"])


@router.post("/{agent_id}/{team_id}", status_code=status.HTTP_201_CREATED)
def add_agent_team(
    agent_id: int,
    team_id: int,
    service: AgentTeamService = Depends(get_agent_team_service),
):
    try:
        service.create(agent_id=agent_id, team_id=team_id)
        return None
    except NotFoundError as e:
        # si e.code est un message du style "TEAM_NOT_FOUND" c'est OK,
        # sinon tu peux mettre un detail plus user-friendly
        not_found(e.code)
    except ValueError as e:
        conflict(str(e))


@router.delete("/{agent_id}/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_team(
    agent_id: int,
    team_id: int,
    service: AgentTeamService = Depends(get_agent_team_service),
):
    ok = service.delete(agent_id=agent_id, team_id=team_id)
    if not ok:
        not_found("Membership not found")
    return None


@router.get("/")
def search_agent_teams(
    agent_id: int | None = Query(None),
    team_id: int | None = Query(None),
    service: AgentTeamService = Depends(get_agent_team_service),
):
    items = service.search(agent_id=agent_id, team_id=team_id)
    return [to_agent_team_dto(x) for x in items]
