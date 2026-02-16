from __future__ import annotations

from datetime import date
from typing import List, Tuple

from backend.app.dto.rh.rh_validation_day_details import (
    RhValidationPosteDayAgentDTO,
    RhValidationPosteDayDetailsDTO,
)
from backend.app.mappers.rh.rh_day_filtering import filter_violations_for_day
from backend.app.mappers.rh.rh_validation_result import rh_violation_to_dto

from core.rh_rules.models.rule_result import RuleResult
from core.utils.severity import Severity


def to_poste_day_details_dto(
    *,
    poste_id: int,
    day: date,
    profile,
    qualified_agent_ids: List[int],
    per_agent_results: List[Tuple[int, RuleResult]],
    include_info: bool,
) -> RhValidationPosteDayDetailsDTO:

    agents: List[RhValidationPosteDayAgentDTO] = []

    for agent_id, result in per_agent_results:
        v_day = filter_violations_for_day(result.violations, day)

        # --- filtrage include_info ---
        if not include_info:
            v_day = [v for v in v_day if v.severity != Severity.INFO]

        # --- tri par sévérité ---
        severity_order = {
            Severity.ERROR: 0,
            Severity.WARNING: 1,
            Severity.INFO: 2,
        }
        v_day.sort(key=lambda v: severity_order.get(v.severity, 99))

        errors_count = sum(1 for v in v_day if v.severity == Severity.ERROR)
        warnings_count = sum(1 for v in v_day if v.severity == Severity.WARNING)
        infos_count = sum(1 for v in v_day if v.severity == Severity.INFO)

        is_valid_day = errors_count == 0

        agents.append(
            RhValidationPosteDayAgentDTO(
                agent_id=agent_id,
                is_valid=is_valid_day,
                errors_count=errors_count,
                warnings_count=warnings_count,
                infos_count=infos_count,
                violations=[rh_violation_to_dto(v) for v in v_day],
            )
        )

    # tri agents : d'abord ceux en erreur
    agents.sort(key=lambda a: (a.is_valid, -a.errors_count))

    return RhValidationPosteDayDetailsDTO(
        poste_id=poste_id,
        date=day,
        profile=getattr(profile, "value", str(profile)),
        eligible_agents_count=len(qualified_agent_ids),
        agents=agents,
    )