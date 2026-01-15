from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_poste_service, get_tranche_service
from backend.app.dto.common.pagination import build_page, Page, PaginationParams, pagination_params
from backend.app.dto.postes import (
    PosteDTO, 
    PosteDetailDTO,
    PosteCreateDTO,
    PosteUpdateDTO
)
from backend.app.mappers.postes import to_poste_dto, to_poste_detail_dto
from backend.app.dto.tranches import (
    TrancheDTO
)
from backend.app.mappers.tranches import to_tranche_dto
from core.application.services import PosteService, TrancheService

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