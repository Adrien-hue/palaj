from __future__ import annotations

from collections.abc import Mapping
from typing import Iterable, Set, Tuple
from datetime import date

from .models import BaselineGroup


GroupKey = Tuple[int, date, int]


def compute_modifications(
    baseline_groups: Iterable[BaselineGroup],
    solution_assignments: Mapping[GroupKey, Set[int]],
) -> int:
    """
    Calcule le nombre de modifications selon la règle du lot 0/1 :

    Pour chaque groupe g=(poste_id,date,tranche_id):
      mods_g = |baseline_agents_g - solution_agents_g|
    Total = somme(mods_g)

    solution_assignments: mapping (poste_id,date,tranche_id) -> set(agent_id)
    """
    total = 0
    for g in baseline_groups:
        sol_agents = solution_assignments.get(g.key, set())
        total += len(g.agents - sol_agents)
    return total
