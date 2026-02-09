from fastapi import APIRouter, Depends

from backend.app.api.deps import get_poste_coverage_requirement_service, get_tranche_service
from backend.app.api.http_exceptions import bad_request, unprocessable_entity
from backend.app.dto.poste_coverage_requirement import PosteCoverageDTO, PosteCoveragePutDTO
from backend.app.mappers.poste_coverage_requirement import poste_coverage_dto_to_entity, to_poste_coverage_dto
from core.application.services import TrancheService
from core.application.services.poste_coverage_requirement_service import PosteCoverageRequirementService

router = APIRouter(prefix="/postes", tags=["Postes - Coverage"])


@router.get("/{poste_id}/coverage", response_model=PosteCoverageDTO)
def get_poste_coverage(
    poste_id: int,
    poste_coverage_requirement_service: PosteCoverageRequirementService = Depends(get_poste_coverage_requirement_service),
    tranche_service: TrancheService = Depends(get_tranche_service),
):
    reqs = poste_coverage_requirement_service.get_for_poste(poste_id)
    tranches = tranche_service.list_by_poste_id(poste_id)
    return to_poste_coverage_dto(poste_id, tranches, reqs)


@router.put("/{poste_id}/coverage", response_model=PosteCoverageDTO)
def put_poste_coverage(
    poste_id: int,
    payload: PosteCoveragePutDTO,
    poste_coverage_requirement_service: PosteCoverageRequirementService = Depends(get_poste_coverage_requirement_service),
    tranche_service: TrancheService = Depends(get_tranche_service),
):
    # garde-fou simple: le poste_id URL est la source de vérité
    if payload.poste_id != poste_id:
        bad_request("poste_id mismatch between path and body")

    entities = [poste_coverage_dto_to_entity(poste_id, r) for r in payload.requirements]

    try:
        saved = poste_coverage_requirement_service.replace_for_poste(poste_id, entities)
    except ValueError as e:
        unprocessable_entity(str(e))

    tranches = tranche_service.list_by_poste_id(poste_id)
    return to_poste_coverage_dto(poste_id, tranches, saved)
