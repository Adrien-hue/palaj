from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_poste_service
from backend.app.dto.postes import PosteListDTO, PosteDetailDTO
from backend.app.mappers.postes import to_poste_list_item_dto, to_poste_detail_dto
from core.application.services import PosteService 

router = APIRouter(prefix="/postes", tags=["Postes"])

@router.get("", response_model=PosteListDTO)
def list_postes(poste_service : PosteService = Depends(get_poste_service)) -> PosteListDTO:
    postes = poste_service.list_all()

    return PosteListDTO(
        items=[to_poste_list_item_dto(p) for p in postes],
        total=len(postes),
    )

@router.get("/{poste_id}", response_model=PosteDetailDTO)
def get_poste(poste_id: int, poste_service : PosteService = Depends(get_poste_service)) -> PosteDetailDTO:
    poste = poste_service.get_poste_complet(poste_id)

    if poste is None:
        raise HTTPException(status_code=404, detail="Poste not found")

    return to_poste_detail_dto(poste)
