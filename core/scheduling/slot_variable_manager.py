from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date
from typing import Any, Dict, List, Tuple

from ortools.sat.python import cp_model

from core.domain.entities.affectation import Affectation
from core.domain.entities.tranche import Tranche


@dataclass(frozen=True)
class Slot:
    """
    Slot à couvrir : une tranche (liée à un poste) sur un jour donné.
    """
    jour: Date
    tranche: Tranche


class SlotVariableManager:
    """
    Variables OR-Tools pour :
      x[a, s] = 1 si l'agent a est affecté au slot s (jour + tranche).

    - a : index agent (dans self.agents)
    - s : index slot (dans self.slots)
    """

    def __init__(
        self,
        model: cp_model.CpModel,
        agents: List[Any],          # tes Agent (au moins .id)
        jours: List[Date],
        tranches: List[Tranche],
    ) -> None:
        self.model = model
        self.agents = list(agents)
        self.jours = list(jours)
        self.tranches = list(tranches)

        # Construction des slots : tous les (jour x tranche)
        self.slots: List[Slot] = [Slot(jour=j, tranche=t) for j in self.jours for t in self.tranches]

        # x[(a, s)] -> BoolVar
        self.x: Dict[Tuple[int, int], cp_model.IntVar] = {}

    def create_variables(self) -> Dict[Tuple[int, int], cp_model.IntVar]:
        """
        Crée x[a, s] pour tous agents et slots.
        """
        for a, agent in enumerate(self.agents):
            for s, slot in enumerate(self.slots):
                # Nom debug : x_{agent_id}_{jour}_{tranche_id}
                var_name = f"x_{agent.id}_{slot.jour.isoformat()}_{slot.tranche.id}"
                self.x[(a, s)] = self.model.NewBoolVar(var_name)
        return self.x

    def get_var(self, a: int, s: int) -> cp_model.IntVar:
        return self.x[(a, s)]

    def iter_indexed(self):
        """Itère sur ((a, s), var)."""
        for key, var in self.x.items():
            yield key, var

    def decode_solution_as_affectations(self, solver: cp_model.CpSolver) -> List[Affectation]:
        """
        Décode la solution en List[Affectation(agent_id, tranche_id, jour)].
        """
        affectations: List[Affectation] = []

        for (a, s), var in self.x.items():
            if solver.Value(var) == 1:
                agent = self.agents[a]
                slot = self.slots[s]
                affectations.append(
                    Affectation(agent_id=agent.id, tranche_id=slot.tranche.id, jour=slot.jour)
                )

        return affectations
