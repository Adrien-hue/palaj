from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_regime_service
from backend.app.dto.common.pagination import build_page, Page, PaginationParams, pagination_params
from backend.app.dto.regimes import RegimeDTO, RegimeDetailDTO
from backend.app.mappers.regimes import to_regime_detail_dto
from core.application.services import RegimeService 

router = APIRouter(prefix="/regimes", tags=["Regimes"])

@router.get("/{regime_id}", response_model=RegimeDetailDTO)
def get_regime(regime_id: int, regime_service : RegimeService = Depends(get_regime_service)) -> RegimeDetailDTO:
    regime = regime_service.get_regime_complet(regime_id)

    if regime is None:
        raise HTTPException(status_code=404, detail="Regime not found")

    return to_regime_detail_dto(regime)

@router.get("/", response_model=Page[RegimeDTO])
def list_agents(
    regime_service: RegimeService = Depends(get_regime_service),
    p: PaginationParams = Depends(pagination_params)
):
    items = regime_service.list(limit=p.limit, offset=p.offset)
    total = regime_service.count()
    return build_page(items=items, total=total, p=p)