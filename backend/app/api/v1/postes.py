from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_poste_service
from backend.app.dto.common.pagination import build_page, Page, PaginationParams, pagination_params
from backend.app.dto.postes import PosteDTO, PosteDetailDTO
from backend.app.mappers.postes import to_poste_detail_dto
from core.application.services import PosteService 

router = APIRouter(prefix="/postes", tags=["Postes"])

@router.get("/{poste_id}", response_model=PosteDetailDTO)
def get_poste(poste_id: int, poste_service : PosteService = Depends(get_poste_service)) -> PosteDetailDTO:
    poste = poste_service.get_poste_complet(poste_id)

    if poste is None:
        raise HTTPException(status_code=404, detail="Poste not found")

    return to_poste_detail_dto(poste)

@router.get("/", response_model=Page[PosteDTO])
def list_agents(
    poste_service: PosteService = Depends(get_poste_service),
    p: PaginationParams = Depends(pagination_params)
):
    items = poste_service.list(limit=p.limit, offset=p.offset)
    total = poste_service.count()
    return build_page(items=items, total=total, p=p)