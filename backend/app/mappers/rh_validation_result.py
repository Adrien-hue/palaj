from backend.app.dto.rh_validation_result import RhValidationResultDTO
from backend.app.mappers.rh_violation import rh_violation_to_dto


def rh_validation_result_to_dto(result) -> RhValidationResultDTO:
    return RhValidationResultDTO(
        is_valid=result.is_valid,
        violations=[rh_violation_to_dto(v) for v in result.violations],
    )
