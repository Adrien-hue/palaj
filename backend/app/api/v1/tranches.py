from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import time

from backend.app.api.deps import get_tranche_service
from backend.app.dto.common.pagination import build_page, Page, PaginationParams, pagination_params
from backend.app.dto.tranches import TrancheDTO, TrancheCreateDTO, TrancheUpdateDTO
from backend.app.mappers.tranches import to_tranche_dto
from core.application.services import TrancheService

router = APIRouter(prefix="/tranches", tags=["Tranches"])


@router.get("/{tranche_id}", response_model=TrancheDTO)
def get_tranche(tranche_id: int, tranche_service: TrancheService = Depends(get_tranche_service)) -> TrancheDTO:
    tranche = tranche_service.get_by_id(tranche_id)
    if tranche is None:
        raise HTTPException(status_code=404, detail="Tranche not found")
    return to_tranche_dto(tranche)


@router.get("/", response_model=Page[TrancheDTO])
def list_tranches(
    tranche_service: TrancheService = Depends(get_tranche_service),
    p: PaginationParams = Depends(pagination_params),
):
    items = tranche_service.list(limit=p.limit, offset=p.offset)
    total = tranche_service.count()
    return build_page(items=items, total=total, p=p)


@router.post("/", response_model=TrancheDTO, status_code=status.HTTP_201_CREATED)
def create_tranche(payload: TrancheCreateDTO, tranche_service: TrancheService = Depends(get_tranche_service)) -> TrancheDTO:
    try:
        tranche = tranche_service.create(**payload.model_dump())
        return to_tranche_dto(tranche)
    except ValueError as e:
        # ex: poste not found, tranche overlap rules, duplicate name, etc.
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/{tranche_id}", response_model=TrancheDTO)
def update_tranche(
    tranche_id: int,
    payload: TrancheUpdateDTO,
    tranche_service: TrancheService = Depends(get_tranche_service),
) -> TrancheDTO:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        tranche = tranche_service.update(tranche_id, **changes)
        if tranche is None:
            raise HTTPException(status_code=404, detail="Tranche not found")
        return to_tranche_dto(tranche)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{tranche_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tranche(tranche_id: int, tranche_service: TrancheService = Depends(get_tranche_service)):
    try:
        ok = tranche_service.delete(tranche_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Tranche not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
