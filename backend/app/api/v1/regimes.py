from fastapi import APIRouter, Depends, status

from backend.app.api.deps import get_regime_service
from backend.app.api.http_exceptions import bad_request, conflict, not_found
from backend.app.dto.common.pagination import Page, PaginationParams, build_page, pagination_params
from backend.app.dto.regimes import RegimeCreateDTO, RegimeDTO, RegimeDetailDTO, RegimeUpdateDTO
from backend.app.mappers.regimes import to_regime_detail_dto
from backend.app.mappers.regimes_light import to_regime_dto
from core.application.services import RegimeService

router = APIRouter(prefix="/regimes", tags=["Regimes"])


@router.post("/", response_model=RegimeDTO, status_code=status.HTTP_201_CREATED)
def create_regime(
    payload: RegimeCreateDTO,
    regime_service: RegimeService = Depends(get_regime_service),
) -> RegimeDTO:
    try:
        regime = regime_service.create(**payload.model_dump())
        return to_regime_dto(regime)
    except ValueError as e:
        conflict(str(e))


@router.delete("/{regime_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_regime(
    regime_id: int,
    regime_service: RegimeService = Depends(get_regime_service),
):
    try:
        ok = regime_service.delete(regime_id)
        if not ok:
            not_found("Regime not found")
        return None
    except ValueError as e:
        conflict(str(e))


@router.get("/{regime_id}", response_model=RegimeDetailDTO)
def get_regime(
    regime_id: int,
    regime_service: RegimeService = Depends(get_regime_service),
) -> RegimeDetailDTO:
    regime = regime_service.get_regime_complet(regime_id)
    if regime is None:
        not_found("Regime not found")
    return to_regime_detail_dto(regime)


@router.get("/", response_model=Page[RegimeDTO])
def list_regimes(
    regime_service: RegimeService = Depends(get_regime_service),
    p: PaginationParams = Depends(pagination_params),
):
    items = regime_service.list(limit=p.limit, offset=p.offset)
    total = regime_service.count()
    return build_page(items=items, total=total, p=p)


@router.patch("/{regime_id}", response_model=RegimeDTO)
def update_regime(
    regime_id: int,
    payload: RegimeUpdateDTO,
    regime_service: RegimeService = Depends(get_regime_service),
) -> RegimeDTO:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        bad_request("No fields to update")

    try:
        regime = regime_service.update(regime_id, **changes)
        if regime is None:
            not_found("Regime not found")
        return to_regime_dto(regime)
    except ValueError as e:
        conflict(str(e))
