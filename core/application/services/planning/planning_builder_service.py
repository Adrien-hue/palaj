from datetime import date
from typing import Dict

from core.domain.entities import Tranche
from core.domain.models.agent_planning import AgentPlanning

from db.repositories.agent_repo import AgentRepository
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.tranche_repo import TrancheRepository


class PlanningBuilderService:
    """
    Service applicatif responsable de construire un AgentPlanning
    à partir de la base SQLite.
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        affectation_repo: AffectationRepository,
        etat_repo: EtatJourAgentRepository,
        tranche_repo: TrancheRepository,
    ):
        self.agent_repo = agent_repo
        self.affectation_repo = affectation_repo
        self.etat_repo = etat_repo
        self.tranche_repo = tranche_repo

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def build_agent_planning(
        self,
        agent_id: int,
        start_date: date,
        end_date: date
    ) -> AgentPlanning:

        agent = self.agent_repo.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} introuvable.")

        etats = [
            e for e in self.etat_repo.list_for_agent(agent_id)
            if start_date <= e.jour <= end_date
        ]

        affectations = [
            a for a in self.affectation_repo.list_for_agent(agent_id)
            if start_date <= a.jour <= end_date
        ]

        tranche_ids = {a.tranche_id for a in affectations if a.tranche_id is not None}

        tranches_by_id: Dict[int, Tranche] = {}
        for tid in tranche_ids:
            tranche = self.tranche_repo.get(tid)
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
