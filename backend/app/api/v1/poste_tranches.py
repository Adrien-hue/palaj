from fastapi import APIRouter, Depends

from backend.app.api.deps import get_tranche_service
from backend.app.api.http_exceptions import not_found
from backend.app.dto.tranches import TrancheDTO
from backend.app.mappers.tranches import to_tranche_dto
from core.application.services import TrancheService

router = APIRouter(prefix="/postes", tags=["Postes - Tranches"])


@router.get("/{poste_id}/tranches", response_model=list[TrancheDTO])
def list_tranches_for_poste(
    poste_id: int,
    tranche_service: TrancheService = Depends(get_tranche_service),
) -> list[TrancheDTO]:
    try:
        items = tranche_service.list_by_poste_id(poste_id)
    except ValueError as e:
        # ton service semble lever ValueError quand poste inconnu
        not_found(str(e))

    return [to_tranche_dto(t) for t in items]
