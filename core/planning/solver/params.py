from __future__ import annotations

from dataclasses import dataclass

from .models import PlanningMode


@dataclass(frozen=True, slots=True)
class SolverParams:
    time_limit_s: float = 10.0
    num_workers: int | None = None
    enable_log: bool = False

    # Optionnel (peut être None pour désactiver)
    max_consecutive_days: int | None = 6


def weights_for_mode(mode: PlanningMode) -> tuple[int, int]:
    """
    (P_uncovered, P_change) selon lot 0/2.
    """
    if mode == PlanningMode.REPAIR:
        return (10000, 1000)
    return (10000, 100)
