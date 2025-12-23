# core/application/services/regime_service.py
from typing import List, Optional

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

    def count(self) -> int:
        return self.regime_repo.count()

    def get_by_id(self, regime_id: int) -> Regime | None:
        return self.regime_repo.get_by_id(regime_id)

    def list(self, *, limit: Optional[int] = None, offset: int = 0) -> List[Regime]:
        return self.regime_repo.list(limit=limit, offset=offset)

    def list_all(self) -> List[Regime]:
        return self.regime_repo.list_all()

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

        return self._enrich_regime(regime)

    def list_regimes_complets(
        self, *, limit: Optional[int] = None, offset: int = 0
    ) -> List[Regime]:
        """Retourne tous les régimes sous forme d'entités métier."""
        regimes = self.regime_repo.list(limit=limit, offset=offset)

        return [self._enrich_regime(regime) for regime in regimes]
    
    def _enrich_regime(self, regime: Regime) -> Regime:
        regime.set_agents(self.agent_repo.list_by_regime_id(regime.id))

        return regime