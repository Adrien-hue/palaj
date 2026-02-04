from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import get_poste_coverage_requirement_service, get_poste_planning_factory, get_poste_service, get_tranche_service
from backend.app.dto.common.pagination import build_page, Page, PaginationParams, pagination_params
from backend.app.dto.poste_coverage_day import PosteCoverageDayDTO
from backend.app.dto.poste_coverage_requirement import (
    PosteCoverageDTO,
    PosteCoveragePutDTO
)
from backend.app.dto.poste_planning import PostePlanningResponseDTO
from backend.app.dto.postes import (
    PosteDTO, 
    PosteDetailDTO,
    PosteCreateDTO,
    PosteUpdateDTO
)
from backend.app.mappers.poste_coverage_day import to_poste_coverage_day_dto
from backend.app.mappers.poste_coverage_requirement import poste_coverage_dto_to_entity, to_poste_coverage_dto
from backend.app.mappers.poste_planning import to_poste_planning_response
from backend.app.mappers.postes import to_poste_dto, to_poste_detail_dto
from backend.app.dto.tranches import (
    TrancheDTO
)
from backend.app.mappers.tranches import to_tranche_dto
from core.application.services import PosteService, TrancheService
from core.application.services.exceptions import NotFoundError
from core.application.services.planning.poste_planning_factory import PostePlanningFactory
from core.application.services.poste_coverage_requirement_service import PosteCoverageRequirementService

router = APIRouter(prefix="/postes", tags=["Postes"])

@router.post("/", response_model=PosteDTO, status_code=status.HTTP_201_CREATED)
def create_poste(payload: PosteCreateDTO, poste_service: PosteService = Depends(get_poste_service)) -> PosteDTO:
    poste = poste_service.create(**payload.model_dump())
    return to_poste_dto(poste)

@router.delete("/{poste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poste(poste_id: int, poste_service: PosteService = Depends(get_poste_service)):
    try:
        ok = poste_service.delete(poste_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Poste not found")
        return None
    except ValueError as e:
        # ex: poste lié à des tranches -> suppression refusée (stratégie 1)
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/{poste_id}", response_model=PosteDetailDTO)
def get_poste(poste_id: int, poste_service : PosteService = Depends(get_poste_service)) -> PosteDetailDTO:
    poste = poste_service.get_poste_complet(poste_id)

    if poste is None:
        raise HTTPException(status_code=404, detail="Poste not found")

    return to_poste_detail_dto(poste)

@router.get("/", response_model=Page[PosteDTO])
def list_postes(
    poste_service: PosteService = Depends(get_poste_service),
    p: PaginationParams = Depends(pagination_params)
):
    items = poste_service.list(limit=p.limit, offset=p.offset)
    total = poste_service.count()
    return build_page(items=items, total=total, p=p)

@router.get("/{poste_id}/tranches", response_model=list[TrancheDTO])
def list_tranches_for_poste(
    poste_id: int,
    tranche_service: TrancheService = Depends(get_tranche_service),
) -> list[TrancheDTO]:
    try:
        items = tranche_service.list_by_poste_id(poste_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return [to_tranche_dto(t) for t in items]

@router.get("/{poste_id}/coverage", response_model=PosteCoverageDTO)
def get_poste_coverage(
    poste_id: int,
    poste_coverage_requirement_service: PosteCoverageRequirementService = Depends(get_poste_coverage_requirement_service),
    tranche_service: TrancheService = Depends(get_tranche_service),
):
    reqs = poste_coverage_requirement_service.get_for_poste(poste_id)
    tranches = tranche_service.list_by_poste_id(poste_id)
    return to_poste_coverage_dto(poste_id, tranches, reqs)


@router.put("/{poste_id}/coverage", response_model=PosteCoverageDTO)
def put_poste_coverage(
    poste_id: int,
    payload: PosteCoveragePutDTO,
    poste_coverage_requirement_service: PosteCoverageRequirementService = Depends(get_poste_coverage_requirement_service),
    tranche_service: TrancheService = Depends(get_tranche_service),
):
    # garde-fou simple: le poste_id URL est la source de vérité
    if payload.poste_id != poste_id:
        raise HTTPException(status_code=400, detail="poste_id mismatch between path and body")

    entities = [poste_coverage_dto_to_entity(poste_id, r) for r in payload.requirements]

    try:
        saved = poste_coverage_requirement_service.replace_for_poste(poste_id, entities)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    tranches = tranche_service.list_by_poste_id(poste_id)
    return to_poste_coverage_dto(poste_id, tranches, saved)

@router.get("/{poste_id}/planning", response_model=PostePlanningResponseDTO)
def get_poste_planning(
    poste_id: int,
    start_date: date = Query(..., description="YYYY-MM-DD"),
    end_date: date = Query(..., description="YYYY-MM-DD"),
    poste_planning_factory: PostePlanningFactory = Depends(get_poste_planning_factory),
):
    try:
        planning = poste_planning_factory.build(
            poste_id=poste_id,
            start_date=start_date,
            end_date=end_date,
        )
        return to_poste_planning_response(planning)
    except ValueError as e:
        msg = str(e)
        # on distingue 404 vs 400 comme tu fais ailleurs
        if msg.lower() == "poste not found":
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    
@router.get("/{poste_id}/planning/coverage", response_model=PosteCoverageDayDTO)
def get_poste_planning_coverage(
    poste_id: int,
    date: date,
    service: PosteService = Depends(get_poste_service),
) -> PosteCoverageDayDTO:
    try:
        rm = service.get_poste_coverage_for_day(poste_id=poste_id, day_date=date)
        return to_poste_coverage_day_dto(rm)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "details": e.details})

@router.patch("/{poste_id}", response_model=PosteDTO)
def update_poste(
    poste_id: int,
    payload: PosteUpdateDTO,
    poste_service: PosteService = Depends(get_poste_service),
) -> PosteDTO:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")

    poste = poste_service.update(poste_id, **changes)
    if poste is None:
        raise HTTPException(status_code=404, detail="Poste not found")

    return to_poste_dto(poste)