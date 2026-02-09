from fastapi import APIRouter, Depends, status

from backend.app.api.deps import get_poste_service
from backend.app.api.http_exceptions import bad_request, conflict, not_found
from backend.app.dto.common.pagination import Page, PaginationParams, build_page, pagination_params
from backend.app.dto.postes import PosteCreateDTO, PosteDTO, PosteDetailDTO, PosteUpdateDTO
from backend.app.mappers.postes import to_poste_detail_dto, to_poste_dto
from core.application.services import PosteService

router = APIRouter(prefix="/postes", tags=["Postes"])


@router.post("/", response_model=PosteDTO, status_code=status.HTTP_201_CREATED)
def create_poste(payload: PosteCreateDTO, poste_service: PosteService = Depends(get_poste_service)) -> PosteDTO:
    poste = poste_service.create(**payload.model_dump())
    return to_poste_dto(poste)


@router.get("/", response_model=Page[PosteDTO])
def list_postes(
    poste_service: PosteService = Depends(get_poste_service),
    p: PaginationParams = Depends(pagination_params),
):
    items = poste_service.list(limit=p.limit, offset=p.offset)
    total = poste_service.count()
    return build_page(items=items, total=total, p=p)


@router.get("/{poste_id}", response_model=PosteDetailDTO)
def get_poste(poste_id: int, poste_service: PosteService = Depends(get_poste_service)) -> PosteDetailDTO:
    poste = poste_service.get_poste_complet(poste_id)
    if poste is None:
        not_found("Poste not found")
    return to_poste_detail_dto(poste)


@router.patch("/{poste_id}", response_model=PosteDTO)
def update_poste(
    poste_id: int,
    payload: PosteUpdateDTO,
    poste_service: PosteService = Depends(get_poste_service),
) -> PosteDTO:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        bad_request("No fields to update")

    poste = poste_service.update(poste_id, **changes)
    if poste is None:
        not_found("Poste not found")

    return to_poste_dto(poste)


@router.delete("/{poste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poste(poste_id: int, poste_service: PosteService = Depends(get_poste_service)):
    try:
        ok = poste_service.delete(poste_id)
        if not ok:
            not_found("Poste not found")
        return None
    except ValueError as e:
        conflict(str(e))
