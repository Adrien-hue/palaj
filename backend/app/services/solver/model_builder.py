from __future__ import annotations

from datetime import timedelta

from backend.app.services.solver.model_artifacts import SolveContext
from backend.app.services.solver.models import SolverInput


def build_solve_context(solver_input: SolverInput) -> SolveContext:
    """Build immutable solve context only (no stats mutation, no model mutation).

    Ordering note: ``ordered_agent_ids`` intentionally keeps the legacy
    ``sorted(solver_input.agent_ids)`` behavior from the former monolith.
    """
    ordered_agent_ids = sorted(solver_input.agent_ids)
    dates = []
    cursor = solver_input.start_date
    while cursor <= solver_input.end_date:
        dates.append(cursor)
        cursor += timedelta(days=1)
    date_to_index = {d: i for i, d in enumerate(dates)}

    apply_gpt_rules = bool(solver_input.gpt_context_days)
    context_days = list(solver_input.gpt_context_days) if apply_gpt_rules else list(dates)
    ctx_date_to_index = {d: i for i, d in enumerate(context_days)}
    in_window_ctx_indices = {ctx_date_to_index[d] for d in dates if d in ctx_date_to_index}

    return SolveContext(
        ordered_agent_ids=ordered_agent_ids,
        dates=dates,
        date_to_index=date_to_index,
        context_days=context_days,
        ctx_date_to_index=ctx_date_to_index,
        in_window_ctx_indices=in_window_ctx_indices,
        apply_gpt_rules=apply_gpt_rules,
        time_limit_seconds=float(solver_input.time_limit_seconds or 0.0),
        profile=(solver_input.quality_profile or "balanced").lower(),
    )
