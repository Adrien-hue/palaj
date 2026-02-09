from fastapi import APIRouter, Depends, Query, status

from backend.app.api.deps import get_qualification_service
from backend.app.api.http_exceptions import bad_request, conflict, not_found
from backend.app.dto.qualifications import QualificationDTO, QualificationCreateDTO, QualificationUpdateDTO
from backend.app.mappers.qualifications import to_qualification_dto
from core.application.services.qualification_service import QualificationService

router = APIRouter(prefix="/qualifications", tags=["Qualifications"])


@router.post("/", response_model=QualificationDTO, status_code=status.HTTP_201_CREATED)
def create_qualification(
    payload: QualificationCreateDTO,
    service: QualificationService = Depends(get_qualification_service),
):
    try:
        q = service.create(**payload.model_dump())
        return to_qualification_dto(q)
    except ValueError as e:
        conflict(str(e))


@router.delete("/{agent_id}/{poste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qualification(
    agent_id: int,
    poste_id: int,
    service: QualificationService = Depends(get_qualification_service),
):
    ok = service.delete(agent_id=agent_id, poste_id=poste_id)
    if not ok:
        not_found("Qualification not found")
    return None


@router.patch("/{agent_id}/{poste_id}", response_model=QualificationDTO)
def update_qualification(
    agent_id: int,
    poste_id: int,
    payload: QualificationUpdateDTO,
    service: QualificationService = Depends(get_qualification_service),
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        bad_request("No fields to update")

    q = service.update(agent_id=agent_id, poste_id=poste_id, **changes)
    if q is None:
        not_found("Qualification not found")

    return to_qualification_dto(q)


@router.get("/", response_model=list[QualificationDTO])
def search_qualifications(
    agent_id: int | None = Query(None),
    poste_id: int | None = Query(None),
    service: QualificationService = Depends(get_qualification_service),
):
    items = service.search(agent_id=agent_id, poste_id=poste_id)
    return [to_qualification_dto(x) for x in items]
