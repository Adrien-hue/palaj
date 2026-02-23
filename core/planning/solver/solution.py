from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple


GroupKey = Tuple[int, date, int]  # (poste_id, date, tranche_id)


@dataclass(frozen=True, slots=True)
class PlanningSolution:
    status: str  # OPTIMAL / FEASIBLE / INFEASIBLE / MODEL_INVALID
    objective_value: int

    # (agent_id, slot_id)
    assignments: List[Tuple[int, int]]

    # slot_id list
    uncovered_slot_ids: List[int]

    # Only for REPAIR (empty otherwise)
    change_count_by_group: Dict[GroupKey, int]


def group_assignments_by_key(
    *,
    assignments: List[Tuple[int, int]],
    slot_key_by_id: Dict[int, GroupKey],
) -> Dict[GroupKey, set[int]]:
    """
    Utility: (agent_id, slot_id) -> group_key -> set(agent_id)
    """
    out: Dict[GroupKey, set[int]] = {}
    for agent_id, slot_id in assignments:
        key = slot_key_by_id[slot_id]
        out.setdefault(key, set()).add(agent_id)
    return out
