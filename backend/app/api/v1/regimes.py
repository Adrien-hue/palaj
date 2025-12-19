from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_regime_service
from backend.app.dto.regimes import RegimeListDTO, RegimeDetailDTO
from backend.app.mappers.regimes import to_regime_dto, to_regime_detail_dto
from core.application.services import RegimeService 

router = APIRouter(prefix="/regimes", tags=["Regimes"])

@router.get("", response_model=RegimeListDTO)
def list_regimes(regime_service : RegimeService = Depends(get_regime_service)) -> RegimeListDTO:
    regimes = regime_service.list_all()

    return RegimeListDTO(
        regimes=[to_regime_dto(r) for r in regimes],
        total=len(regimes),
    )

@router.get("/{regime_id}", response_model=RegimeDetailDTO)
def get_regime(regime_id: int, regime_service : RegimeService = Depends(get_regime_service)) -> RegimeDetailDTO:
    regime = regime_service.get_regime_complet(regime_id)

    if regime is None:
        raise HTTPException(status_code=404, detail="Regime not found")

    return to_regime_detail_dto(regime)
