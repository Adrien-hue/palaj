from __future__ import annotations

import random
from datetime import timedelta

from core.domain.enums.day_type import DayType

from .models import SolverAgentDay, SolverInput, SolverOutput


class OrtoolsSolver:
    def generate(self, solver_input: SolverInput) -> SolverOutput:
        rng = random.Random(solver_input.seed)
        ordered_agent_ids = sorted(solver_input.agent_ids)
        rng.shuffle(ordered_agent_ids)

        agent_days: list[SolverAgentDay] = []
        cursor = solver_input.start_date
        while cursor <= solver_input.end_date:
            for agent_id in ordered_agent_ids:
                agent_days.append(
                    SolverAgentDay(
                        agent_id=agent_id,
                        day_date=cursor,
                        day_type=DayType.REST.value,
                        description=None,
                        is_off_shift=False,
                    )
                )
            cursor += timedelta(days=1)

        return SolverOutput(
            agent_days=agent_days,
            assignments=[],
            stats={"score": 0, "coverage_ratio": 0, "soft_violations": 0},
        )
