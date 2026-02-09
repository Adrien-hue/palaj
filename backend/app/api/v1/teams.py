from fastapi import APIRouter, Depends, status

from backend.app.api.deps import get_team_service
from backend.app.api.http_exceptions import bad_request, conflict, not_found
from backend.app.dto.common.pagination import Page, PaginationParams, build_page, pagination_params
from backend.app.dto.team import TeamCreateDTO, TeamDTO, TeamUpdateDTO
from backend.app.mappers.teams import to_team_dto
from core.application.services.exceptions import ConflictError, NotFoundError
from core.application.services.teams.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=Page[TeamDTO])
def list_teams(
    service: TeamService = Depends(get_team_service),
    p: PaginationParams = Depends(pagination_params),
):
    items = service.list(limit=p.limit, offset=p.offset)
    total = service.count()
    return build_page(items, total, p)


@router.post("", response_model=TeamDTO, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreateDTO,
    service: TeamService = Depends(get_team_service),
):
    try:
        team = service.create(name=payload.name, description=payload.description)
        # certains services renvoient déjà un DTO; si c’est une entité, mapper ici
        return to_team_dto(team)
    except ConflictError as e:
        conflict(e.code)


@router.get("/{team_id}", response_model=TeamDTO)
def get_team(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    try:
        team = service.get(team_id)
        return to_team_dto(team)
    except NotFoundError as e:
        not_found(e.code)


@router.patch("/{team_id}", response_model=TeamDTO)
def update_team(
    team_id: int,
    payload: TeamUpdateDTO,
    service: TeamService = Depends(get_team_service),
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        bad_request("No fields to update")

    try:
        team = service.update(team_id, **changes)
        if team is None:
            not_found("Team not found")
        return to_team_dto(team)
    except NotFoundError as e:
        not_found(e.code)
    except ConflictError as e:
        conflict(e.code)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    # delete idempotent
    service.delete(team_id)
    return None
