from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import get_team_planning_factory, get_team_service
from backend.app.dto.common.pagination import build_page, Page, PaginationParams, pagination_params
from backend.app.dto.team import TeamCreateDTO, TeamDTO, TeamUpdateDTO
from backend.app.dto.team_planning import TeamPlanningResponseDTO
from backend.app.mappers.team_planning import to_team_planning_response
from backend.app.mappers.teams import to_team_dto
from core.application.services.planning.team_planning_factory import TeamPlanningFactory
from core.application.services.teams.team_service import TeamService
from core.application.services.exceptions import NotFoundError, ConflictError

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=Page[TeamDTO])
def list_teams(
    service: TeamService = Depends(get_team_service),
    p: PaginationParams = Depends(pagination_params)
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
    

@router.get("/{team_id}/planning", response_model=TeamPlanningResponseDTO)
def get_team_planning(
    team_id: int,
    start_date: date = Query(..., description="YYYY-MM-DD"),
    end_date: date = Query(..., description="YYYY-MM-DD"),
    team_planning_factory: TeamPlanningFactory = Depends(get_team_planning_factory),
):
    try:
        planning = team_planning_factory.build(team_id=team_id, start_date=start_date, end_date=end_date)
        return to_team_planning_response(planning)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "details": e.details})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{team_id}", response_model=TeamDTO)
def update_team(
    team_id: int,
    payload: TeamUpdateDTO,
    service: TeamService = Depends(get_team_service),
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        team = service.update(team_id, **changes)
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")
        return to_team_dto(team)
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
