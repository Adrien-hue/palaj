# core/domain/models/poste_planning.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from core.domain.entities import Affectation, Agent, Poste, Tranche  # + Poste si tu as cette entité


@dataclass
class PostePlanning:
    """
    Modèle de domaine : vision complète du planning d'un poste
    sur une période donnée.

    Permet de répondre à :
      - Quel agent couvre telle tranche, tel jour ?
      - Quelles tranches ne sont pas couvertes ?
    """

    poste: Poste
    start_date: date
    end_date: date

    # Données "brutes"
    affectations: List[Affectation]
    tranches: List[Tranche]

    # Période discrétisée jour par jour (utile pour les viewers)
    dates: List[date]

    # Index interne : (jour, tranche_id) -> Agent (ou None si non couvert)
    _agent_by_day_tranche: Dict[Tuple[date, int], Optional[Agent]] = field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Factory principale
    # ------------------------------------------------------------------
    @classmethod
    def build(
        cls,
        poste: Poste,
        start_date: date,
        end_date: date,
        affectations: List[Affectation],
        agents_by_id: Dict[int, Agent],
        tranches_by_id: Dict[int, Tranche],
    ) -> "PostePlanning":
        """
        Construit un PostePlanning à partir :
          - du poste
          - de la période [start_date, end_date]
          - des affectations (normalement filtrées pour ce poste)
          - d'un index agents_by_id (id -> Agent)
          - d'un index tranches_by_id (id -> Tranche) pour ce poste.
        """

        # 1) Liste des dates couvertes par la période
        dates: List[date] = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)

        # 2) Index (jour, tranche_id) -> Agent
        agent_by_day_tranche: Dict[Tuple[date, int], Optional[Agent]] = {}

        filtered_affectations: List[Affectation] = []

        for aff in affectations:
            # Filtrage par période
            if aff.jour < start_date or aff.jour > end_date:
                continue

            # On ne garde que les tranches connues dans tranches_by_id
            if aff.tranche_id not in tranches_by_id:
                continue

            filtered_affectations.append(aff)

            agent = agents_by_id.get(aff.agent_id)
            key = (aff.jour, aff.tranche_id)
            # En cas de conflit (plusieurs affectations sur même slot),
            # la dernière écrase la précédente → à adapter si besoin.
            agent_by_day_tranche[key] = agent

        return cls(
            poste=poste,
            start_date=start_date,
            end_date=end_date,
            affectations=filtered_affectations,
            tranches=list(tranches_by_id.values()),
            dates=dates,
            _agent_by_day_tranche=agent_by_day_tranche,
        )

    # ------------------------------------------------------------------
    # Getters / API publique (dans l'esprit d'AgentPlanning)
    # ------------------------------------------------------------------

    def get_poste(self):
        return self.poste

    def get_start_date(self) -> date:
        return self.start_date

    def get_end_date(self) -> date:
        return self.end_date

    def get_nb_jours(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def get_dates(self) -> List[date]:
        return self.dates

    def get_tranches(self) -> List[Tranche]:
        return self.tranches

    def get_affectations(self) -> List[Affectation]:
        return self.affectations

    # ------------------------------------------------------------------
    # Accès clé : qui couvre quoi ?
    # ------------------------------------------------------------------

    def get_agent_for(self, jour: date, tranche: Tranche) -> Optional[Agent]:
        """
        Retourne l'agent affecté à (jour, tranche) pour ce poste,
        ou None si aucune affectation.
        """
        return self._agent_by_day_tranche.get((jour, tranche.id))

    def get_agents_for_day(self, jour: date) -> Dict[Tranche, Optional[Agent]]:
        """
        Retourne un petit dict : tranche -> agent pour un jour donné.
        Pratique pour des usages applicatifs / vues.
        """
        result: Dict[Tranche, Optional[Agent]] = {}
        for t in self.tranches:
            result[t] = self.get_agent_for(jour, t)
        return result

    def get_uncovered_slots(self) -> List[Tuple[date, Tranche]]:
        """
        Retourne la liste de tous les (jour, tranche) non couverts.
        Utile pour les stats ou les alertes.
        """
        uncovered: List[Tuple[date, Tranche]] = []
        for jour in self.dates:
            for t in self.tranches:
                if self.get_agent_for(jour, t) is None:
                    uncovered.append((jour, t))
        return uncovered
