from __future__ import annotations

from datetime import date
from typing import Any

from core.domain.enums.day_type import DayType


def normalize_working_signature(sig: dict[str, Any] | None) -> tuple[int | None, tuple[int, ...]] | None:
    """Return normalized (poste_id, sorted tranche_ids) or None when invalid."""
    if not isinstance(sig, dict):
        return None
    poste_id_raw = sig.get("poste_id")
    tranche_ids_raw = sig.get("tranche_ids")
    try:
        poste_id = int(poste_id_raw) if poste_id_raw is not None else None
    except (TypeError, ValueError):
        return None
    if poste_id is None:
        return None
    if tranche_ids_raw is None:
        return None
    try:
        tranche_ids = tuple(sorted(int(tranche_id) for tranche_id in tranche_ids_raw))
    except (TypeError, ValueError):
        return None
    if not tranche_ids:
        return None
    return poste_id, tranche_ids


def has_working_assignments(sig: dict[str, Any] | None) -> bool:
    if not isinstance(sig, dict):
        return False
    tranche_ids_raw = sig.get("tranche_ids")
    if tranche_ids_raw is None:
        return False
    try:
        return len([int(tranche_id) for tranche_id in tranche_ids_raw]) > 0
    except (TypeError, ValueError):
        return False


def resolve_existing_day_state(
    *,
    agent_id: int,
    day_date: date,
    db_daytype: str | None,
    db_sig: dict[str, Any] | None,
    solver_absent_flag: bool,
) -> dict[str, Any]:
    """Resolve existing day state with deterministic precedence and conflict reasons.

    Resolution rules:
    - DB day type is the source of truth when present.
    - If solver_absent_flag is true but DB day type is not ABSENT, mark conflict.
      Resolved day type stays DB value when present; otherwise fallback to ABSENT.
    - ABSENT/LEAVE ignore signature.
    - WORKING expects a valid signature (poste_id + sorted tranche_ids); missing/invalid
      signature is a conflict, but resolved day type remains WORKING.
    """
    normalized_daytype = str(db_daytype).lower() if db_daytype is not None else None
    normalized_signature = normalize_working_signature(db_sig)

    conflict_reasons: list[str] = []
    if solver_absent_flag and normalized_daytype != DayType.ABSENT.value:
        if normalized_daytype is None:
            conflict_reasons.append("solver_absence_without_db_daytype")
        else:
            conflict_reasons.append("solver_absence_conflicts_with_db_daytype")

    if normalized_daytype in {DayType.ABSENT.value, DayType.LEAVE.value}:
        resolved_daytype = normalized_daytype
        normalized_signature = None
    elif normalized_daytype == DayType.WORKING.value:
        resolved_daytype = DayType.WORKING.value
        if normalized_signature is None:
            conflict_reasons.append("working_missing_or_invalid_signature")
    elif normalized_daytype is None:
        resolved_daytype = DayType.ABSENT.value if solver_absent_flag else DayType.REST.value
        normalized_signature = None
    else:
        resolved_daytype = normalized_daytype
        normalized_signature = None

    return {
        "agent_id": agent_id,
        "day_date": day_date,
        "daytype": resolved_daytype,
        "signature": normalized_signature,
        "is_conflict": bool(conflict_reasons),
        "conflict_reason": ",".join(conflict_reasons) if conflict_reasons else None,
        "db_daytype": normalized_daytype,
        "solver_absent_flag": solver_absent_flag,
    }


def is_in_window_ctx_index(ci: int, in_window_ctx_indices: set[int]) -> bool:
    return ci in in_window_ctx_indices


def is_in_window_date(day_date: date, in_window_dates: set[date]) -> bool:
    return day_date in in_window_dates


def build_existing_context_maps(
    *,
    ordered_agent_ids: list[int],
    context_days: list[date],
    db_daytype_by_agent_day_ctx: dict[tuple[int, date], str],
    db_assignment_by_agent_day_ctx: dict[tuple[int, date], dict[str, Any]],
    absences: set[tuple[int, date]],
    max_sample_size: int = 10,
) -> dict[str, Any]:
    resolved_daytype_by_agent_day_ctx: dict[tuple[int, date], str] = {}
    resolved_working_sig_by_agent_day_ctx: dict[tuple[int, date], tuple[int, tuple[int, ...]]] = {}
    conflicts_count = 0
    conflicts_sample: list[dict[str, Any]] = []
    missing_working_assignments_count_total = 0
    missing_working_assignments_sample: list[dict[str, Any]] = []

    for agent_id in ordered_agent_ids:
        for day_date in context_days:
            key = (agent_id, day_date)
            db_sig = db_assignment_by_agent_day_ctx.get(key)
            resolved = resolve_existing_day_state(
                agent_id=agent_id,
                day_date=day_date,
                db_daytype=db_daytype_by_agent_day_ctx.get(key),
                db_sig=db_sig,
                solver_absent_flag=key in absences,
            )
            resolved_daytype_by_agent_day_ctx[key] = resolved["daytype"]
            if resolved["daytype"] == DayType.WORKING.value and resolved["signature"] is not None:
                resolved_working_sig_by_agent_day_ctx[key] = resolved["signature"]

            if resolved["daytype"] == DayType.WORKING.value and not has_working_assignments(db_sig):
                missing_working_assignments_count_total += 1
                if len(missing_working_assignments_sample) < max_sample_size:
                    missing_working_assignments_sample.append(
                        {
                            "agent_id": agent_id,
                            "day_date": day_date.isoformat(),
                        }
                    )

            if resolved["is_conflict"]:
                conflicts_count += 1
                if len(conflicts_sample) < max_sample_size:
                    conflicts_sample.append(
                        {
                            "agent_id": agent_id,
                            "day_date": day_date.isoformat(),
                            "db_daytype": resolved["db_daytype"],
                            "solver_absent_flag": resolved["solver_absent_flag"],
                            "conflict_reason": resolved["conflict_reason"],
                        }
                    )

    return {
        "resolved_daytype_by_agent_day_ctx": resolved_daytype_by_agent_day_ctx,
        "resolved_working_sig_by_agent_day_ctx": resolved_working_sig_by_agent_day_ctx,
        "existing_assignments_conflicts_count": conflicts_count,
        "existing_assignments_conflicts_sample": conflicts_sample,
        "existing_working_missing_assignments_count_total": missing_working_assignments_count_total,
        "existing_working_missing_assignments_sample": missing_working_assignments_sample,
    }
