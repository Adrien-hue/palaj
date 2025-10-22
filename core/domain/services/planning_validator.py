from datetime import date
from typing import List

from core.domain.contexts.planning_context import PlanningContext

from core.utils.logger import Logger

from db.repositories.agent_repo import AgentRepository
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.tranche_repo import TrancheRepository

from models.agent import Agent
from models.tranche import Tranche

from .affectation_service import AffectationService
from .etat_jour_agent_service import EtatJourAgentService
from .rh_rules_service import RHRulesService


class PlanningValidator:
    """
    Façade centrale de validation du planning.
    Vérifie la cohérence entre affectations, états journaliers et règles RH.
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        affectation_repo: AffectationRepository,
        etat_jour_agent_repo: EtatJourAgentRepository,
        tranche_repo: TrancheRepository,
        verbose: bool = False
    ):
        self.agent_repo = agent_repo
        self.affectation_repo = affectation_repo
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.tranche_repo = tranche_repo

        self.affectation_service = AffectationService(agent_repo, affectation_repo, etat_jour_agent_repo, tranche_repo, verbose=verbose)
        self.etat_service = EtatJourAgentService(etat_jour_agent_repo, verbose=verbose)
        self.rh_rules_service = RHRulesService(tranche_repo, affectation_repo)

        self.logger = Logger(verbose=verbose)

    # ------------------------------------------------------------
    def validate_day(self, agent: Agent, jour: date, tranches: List[Tranche], simulate: bool = True) -> List[str]:
        """
        Valide la cohérence d’un jour donné pour un agent.
        Coordonne les vérifications entre services sans dupliquer la logique.
        """
        alerts: List[str] = []

        # 1️⃣ Vérification disponibilité via le service métier
        if tranches and not all(self.affectation_service.can_assign(agent, t, jour) for t in tranches):
            alerts.append(f"[{jour}] 🚫 Agent non disponible (repos / congé / déjà affecté)")
            return alerts

        # 2️⃣ Vérification cohérence État / Affectations
        alerts.extend(self.etat_service.check_coherence(agent, jour, tranches, simulate))

        # 3️⃣ Vérification RH complète via PlanningContext
        context = PlanningContext.from_repositories(
            agent=agent,
            jour=jour,
            affectation_repo=self.affectation_repo,
            etat_repo=self.etat_service.etat_repo
        )
        alerts.extend(self.rh_rules_service.check_all(context))

        # 4️⃣ Sanity check local (sécurité)
        if len(tranches) > 1:
            tranche_names = ", ".join(t.abbr for t in tranches)
            alerts.append(f"[{jour}] ⚠️ Plusieurs tranches affectées le même jour ({tranche_names})")

        return alerts


    # ------------------------------------------------------------
    def validate_period(
        self,
        agent: Agent,
        jours: List[date],
        tranches_par_jour: dict[date, List[Tranche]],
        simulate: bool = True,
    ) -> List[str]:
        """
        Vérifie la cohérence du planning sur plusieurs jours.
        Retourne la liste agrégée des alertes.
        """
        all_alerts: List[str] = []
        for jour in jours:
            tranches = tranches_par_jour.get(jour, [])
            day_alerts = self.validate_day(agent, jour, tranches, simulate)
            all_alerts.extend(day_alerts)
        return all_alerts
