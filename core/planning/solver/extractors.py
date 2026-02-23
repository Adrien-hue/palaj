from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Iterable, List, Sequence, Set, Tuple, Optional

from .models import (
    BaselineGroup,
    LockType,
    Need,
    PlanningInstance,
    PlanningMode,
    SlotLock,
    SolverAgent,
    SolverSlot,
)

from .constants import UNAVAILABLE_DAY_TYPES

# ---------- Needs -> Slots ----------

def expand_needs_to_slots(needs: Sequence[Need]) -> List[SolverSlot]:
    """
    Déplie les besoins unitaires en slots interchangeables.

    Règles lot 1 :
    - tri déterministe
    - ids déterministes
    """
    # tri: (date, poste_id, tranche_id) => stable + intuitif
    ordered = sorted(needs, key=lambda n: (n.date, n.poste_id, n.tranche_id))

    slots: List[SolverSlot] = []
    slot_id = 0
    for n in ordered:
        if n.required_count <= 0:
            continue
        for _ in range(n.required_count):
            slots.append(
                SolverSlot(
                    id=slot_id,
                    poste_id=n.poste_id,
                    date=n.date,
                    tranche_id=n.tranche_id,
                )
            )
            slot_id += 1
    return slots


# ---------- Agents ----------

def build_solver_agents(
    agents: Iterable[object],
    agent_days: Optional[Iterable[object]] = None,    
) -> List[SolverAgent]:
    unavailable_by_agent: dict[int, Set[date]] = defaultdict(set)

    if agent_days is not None:
        for d in agent_days:
            dt = (getattr(d, "day_type", None) or "").lower()
            if dt in UNAVAILABLE_DAY_TYPES:
                unavailable_by_agent[int(d.agent_id)].add(d.day_date)

    out: List[SolverAgent] = []
    for a in sorted(list(agents), key=lambda x: int(x.id)):
        quals = set()
        for q in getattr(a, "qualifications", []) or []:
            if hasattr(q, "qualification_id"):
                quals.add(int(q.qualification_id))
            elif hasattr(q, "id"):
                quals.add(int(q.id))

        out.append(
            SolverAgent(
                id=int(a.id),
                qualifications=quals,
                unavailable_dates=unavailable_by_agent.get(int(a.id), set()),
            )
        )
    return out



# ---------- Baseline groups (from AgentDayAssignment) ----------

GroupKey = Tuple[int, date, int]


def build_baseline_groups_from_assignments(
    assignments: Iterable[object],
) -> List[BaselineGroup]:
    """
    Construit la baseline à partir des AgentDayAssignment.

    Attendus:
    - assignment.tranche_id
    - assignment.agent_day.day_date
    - assignment.agent_day.agent_id
    - assignment.tranche.poste_id  (via relation)
    """
    grouped: dict[GroupKey, Set[int]] = defaultdict(set)

    for asg in assignments:
        tranche = getattr(asg, "tranche", None)
        if tranche is None or not hasattr(tranche, "poste_id"):
            raise ValueError("Assignment.tranche doit être chargé et contenir poste_id")

        poste_id = int(tranche.poste_id)
        d = asg.agent_day.day_date
        tranche_id = int(asg.tranche_id)
        agent_id = int(asg.agent_day.agent_id)

        grouped[(poste_id, d, tranche_id)].add(agent_id)

    groups: List[BaselineGroup] = []
    for (poste_id, d, tranche_id), agent_ids in grouped.items():
        groups.append(
            BaselineGroup(
                poste_id=poste_id,
                date=d,
                tranche_id=tranche_id,
                agents=set(agent_ids),
            )
        )

    # tri déterministe
    groups.sort(key=lambda g: (g.date, g.poste_id, g.tranche_id))
    return groups


# ---------- Locks merge ----------

def merge_locks(
    slots: Sequence[SolverSlot],
    mode: PlanningMode,
    user_hard_locks: Optional[dict[int, int]] = None,
    baseline_groups: Optional[Sequence[BaselineGroup]] = None,
) -> List[SlotLock]:
    """
    Lot 1:
    - HARD utilisateur prioritaire
    - Baseline -> SOFT en REPAIR
    - sinon NONE

    user_hard_locks: mapping slot_id -> agent_id (si tu ajoutes plus tard)
    """
    user_hard_locks = user_hard_locks or {}

    baseline_keys = set()
    if mode == PlanningMode.REPAIR and baseline_groups is not None:
        baseline_keys = {g.key for g in baseline_groups if g.agents}

    locks: List[SlotLock] = []
    for s in slots:
        if s.id in user_hard_locks:
            locks.append(SlotLock(slot_id=s.id, lock_type=LockType.HARD, agent_id=int(user_hard_locks[s.id])))
        elif mode == PlanningMode.REPAIR and s.key in baseline_keys:
            locks.append(SlotLock(slot_id=s.id, lock_type=LockType.SOFT, agent_id=None))
        else:
            locks.append(SlotLock(slot_id=s.id, lock_type=LockType.NONE, agent_id=None))
    return locks


# ---------- Build PlanningInstance ----------

def build_planning_instance(
    *,
    mode: PlanningMode,
    needs: Sequence[Need],
    agents: Iterable[object],
    baseline_assignments: Optional[Iterable[object]] = None,
) -> PlanningInstance:
    """
    Construit l'instance canonique, déterministe, sans OR-Tools.
    """
    slots = expand_needs_to_slots(needs)
    solver_agents = build_solver_agents(agents)

    baseline_groups: List[BaselineGroup] = []
    if mode == PlanningMode.REPAIR and baseline_assignments is not None:
        baseline_groups = build_baseline_groups_from_assignments(baseline_assignments)

    locks = merge_locks(
        slots=slots,
        mode=mode,
        user_hard_locks=None,
        baseline_groups=baseline_groups,
    )

    return PlanningInstance(
        agents=solver_agents,
        slots=slots,
        baseline_groups=baseline_groups,
        locks=locks,
        mode=mode,
    )
