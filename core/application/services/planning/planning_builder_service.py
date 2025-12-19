# core/application/services/planning/planning_builder_service.py
from __future__ import annotations
from datetime import date
from typing import Dict, TYPE_CHECKING

from core.domain.entities import Tranche
from core.domain.models.agent_planning import AgentPlanning
from core.domain.models.poste_planning import PostePlanning

if TYPE_CHECKING:
    from core.application.services.affectation_service import AffectationService
    from core.application.services.agent_service import AgentService
    from core.application.services.etat_jour_agent_service import EtatJourAgentService
    from core.application.services.poste_service import PosteService
    from core.application.services.tranche_service import TrancheService


class PlanningBuilderService:
    """
    Service applicatif responsable de construire un AgentPlanning
    à partir de la base SQLite.
    """

    def __init__(
        self,
        affectation_service: AffectationService,
        agent_service: AgentService,
        etat_service: EtatJourAgentService,
        poste_service: PosteService,
        tranche_service: TrancheService,
    ):
        self.affectation_service = affectation_service
        self.agent_service = agent_service
        self.etat_service = etat_service
        self.poste_service = poste_service
        self.tranche_service = tranche_service

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def build_agent_planning(
        self,
        agent_id: int,
        start_date: date,
        end_date: date
    ) -> AgentPlanning:

        agent = self.agent_service.get_agent_complet(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} introuvable.")

        etats = [
            e for e in self.etat_service.list_for_agent(agent_id)
            if start_date <= e.jour <= end_date
        ]

        affectations = [
            a for a in self.affectation_service.list_for_agent(agent_id)
            if start_date <= a.jour <= end_date
        ]

        tranche_ids = {a.tranche_id for a in affectations if a.tranche_id is not None}

        tranches_by_id: Dict[int, Tranche] = {}
        for tid in tranche_ids:
            tranche = self.tranche_service.get_by_id(tid)
            if tranche is not None:
                tranches_by_id[tid] = tranche

        planning = AgentPlanning.build(
            agent=agent,
            start_date=start_date,
            end_date=end_date,
            etats=etats,
            affectations=affectations,
            tranches_by_id=tranches_by_id
        )

        return planning

    def build_poste_planning(
        self,
        poste_id: int,
        start_date: date,
        end_date: date,
    ) -> PostePlanning:
        """
        Construit un PostePlanning pour un poste donné sur la période [start_date, end_date].
        """

        poste = self.poste_service.get_by_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} introuvable.")

        # 1) Récupérer les tranches de ce poste
        tranches = self.tranche_service.list_by_poste_id(poste_id)
        tranches_by_id: Dict[int, Tranche] = {t.id: t for t in tranches}

        if not tranches_by_id:
            raise ValueError(f"Aucune tranche associée au poste {poste.nom}(id: {poste.id}).")

        # 2) Récupérer les affectations pour ce poste et filtrer par période
        affectations = self.affectation_service.list_for_poste(poste_id, start_date, end_date)

        # 3) Construire l'index agents_by_id
        agent_ids = {a.agent_id for a in affectations if getattr(a, "agent_id", None) is not None}

        agents_by_id = {}
        for aid in agent_ids:
            agent = self.agent_service.get_by_id(aid)
            if agent is not None:
                agents_by_id[aid] = agent

        # 4) Construction du PostePlanning via la factory de domaine
        poste_planning = PostePlanning.build(
            poste=poste,
            start_date=start_date,
            end_date=end_date,
            affectations=affectations,
            agents_by_id=agents_by_id,
            tranches_by_id=tranches_by_id,
        )

        return poste_planning