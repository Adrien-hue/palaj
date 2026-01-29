from typing import List

from backend.app.dto.poste_coverage_requirement import PosteCoverageDTO, PosteCoverageRequirementDTO

from backend.app.mappers.tranches import to_tranche_dto

from core.domain.entities import PosteCoverageRequirement

def poste_coverage_dto_to_entity(poste_id: int, dto: PosteCoverageRequirementDTO) -> PosteCoverageRequirement:
    return PosteCoverageRequirement(
        poste_id=poste_id,
        weekday=dto.weekday,
        tranche_id=dto.tranche_id,
        required_count=dto.required_count,
    )

def entities_to_requirement_dtos(
    entities: list[PosteCoverageRequirement],
) -> list[PosteCoverageRequirementDTO]:
    return [
        PosteCoverageRequirementDTO(
            weekday=e.weekday,
            tranche_id=e.tranche_id,
            required_count=e.required_count,
        )
        for e in entities
    ]

def to_poste_coverage_dto(
    poste_id: int,
    tranches,
    req_entities: list[PosteCoverageRequirement],
) -> PosteCoverageDTO:
    return PosteCoverageDTO(
        poste_id=poste_id,
        tranches=[to_tranche_dto(t) for t in tranches],
        requirements=entities_to_requirement_dtos(req_entities),
    )