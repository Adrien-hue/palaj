# core/application/analyzers/poste_planning_analyzer.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, List, Optional, Tuple

from core.application.services.container import poste_service, qualification_service

from core.domain.models.poste_planning import PostePlanning

@dataclass(frozen=True)
class UnqualifiedAssignment:
    jour: date
    tranche_id: int
    tranche_name: str
    agent_id: int
    agent_label: str
    poste_id: int
    poste_name: str


class PostePlanningAnalyzer:
    def __init__(self):
        self.poste_service = poste_service
        self.qualification_service = qualification_service

    def find_unqualified_assignments(self, planning: PostePlanning) -> List[UnqualifiedAssignment]:
        poste = planning.get_poste()

        if poste is None:
            return []

        poste_id = poste.id
        poste_name = poste.nom
        if poste_id is None:
            # Sans poste_id, impossible de faire le lien table qualification
            return []

        # 1) Préchargement des agents qualifiés pour ce poste
        qualified_agents = set(self.qualification_service.list_for_poste(poste_id))

        qualified_agent_ids = {q.agent_id for q in qualified_agents}

        # 2) Scan du planning
        violations: List[UnqualifiedAssignment] = []
        for jour in planning.get_dates():
            for tranche in planning.get_tranches():
                agent = planning.get_agent_for(jour, tranche)
                if agent is None:
                    continue

                agent_id = agent.id

                if agent_id not in qualified_agent_ids:
                    violations.append(
                        UnqualifiedAssignment(
                            jour=jour,
                            tranche_id=tranche.id,
                            tranche_name=tranche.nom,
                            agent_id=agent_id,
                            agent_label=agent.get_full_name(),
                            poste_id=poste_id,
                            poste_name=poste_name,
                        )
                    )

        return violations