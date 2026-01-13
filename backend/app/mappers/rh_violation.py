from backend.app.dto.rh_violation import RhViolationDTO


def rh_violation_to_dto(v) -> RhViolationDTO:
    return RhViolationDTO(
        code=v.code,
        rule=v.rule_name,
        severity=v.severity.value,  # enum → "error" | "warning" | "info"
        message=v.message,
        start_date=v.start_date,
        end_date=v.end_date,
        start_dt=v.start_dt,
        end_dt=v.end_dt,
        meta=v.meta or {},
    )
