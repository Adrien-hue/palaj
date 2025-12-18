# core/application/services/regime_service.py
from typing import List

from core.application.ports import (
    AgentRepositoryPort,
    RegimeRepositoryPort,
)
from core.domain.entities import Regime


class RegimeService:
    """
    Service applicatif :
    - Coordonne le repository des régimes
    - Délègue la validation métier au RegimeValidatorService
    """

    def __init__(
        self,
        agent_repo: AgentRepositoryPort,
        regime_repo: RegimeRepositoryPort,
    ):
        self.agent_repo = agent_repo
        self.regime_repo = regime_repo

    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_regime_complet(self, regime_id: int) -> Regime | None:
        """
        Récupère un régime enrichi avec ses agents.
        """
        regime = self.regime_repo.get_by_id(regime_id)
        if not regime:
            return None

        # Charger les agents
        regime.set_agents(self.agent_repo.list_by_regime_id(regime.id))

        return regime

    def list_regimes_complets(self) -> List[Regime]:
        """Retourne tous les régimes sous forme d'entités métier."""
        regimes = self.regime_repo.list_all()

        for r in regimes:
            r.set_agents(self.agent_repo.list_by_regime_id(r.id))

        return regimes