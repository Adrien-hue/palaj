from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_team_service
from backend.app.dto.team import TeamCreateDTO, TeamDTO, TeamUpdateDTO
from core.application.services.teams.team_service import TeamService
from core.application.services.teams.exceptions import NotFoundError, ConflictError

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=List[TeamDTO])
def list_teams(
    service: TeamService = Depends(get_team_service),
):
    return service.list_all()


@router.post("", response_model=TeamDTO, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreateDTO,
    service: TeamService = Depends(get_team_service),
):
    try:
        return service.create(name=payload.name, description=payload.description)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.code)


@router.get("/{team_id}", response_model=TeamDTO)
def get_team(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    try:
        return service.get(team_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.code)


@router.patch("/{team_id}", response_model=TeamDTO)
def update_team(
    team_id: int,
    payload: TeamUpdateDTO,
    service: TeamService = Depends(get_team_service),
):
    try:
        return service.update(team_id, name=payload.name, description=payload.description)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.code)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.code)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    # delete est idempotent chez toi (ok si déjà supprimé)
    service.delete(team_id)
    return None
