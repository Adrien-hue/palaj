# core/application/services/regime_service.py
from typing import Any, List, Optional

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
    
    def create(
        self,
        *,
        nom: str,
        desc: str = "",

        min_rp_annuels: Optional[int] = None,
        min_rp_dimanches: Optional[int] = None,

        min_rpsd: Optional[int] = None,
        min_rp_2plus: Optional[int] = None,

        min_rp_semestre: Optional[int] = None,

        avg_service_minutes: Optional[int] = None,
        avg_tolerance_minutes: Optional[int] = None,
    ) -> Regime:
        if self.regime_repo.get_by_name(nom):
            raise ValueError("Regime already exists")

        regime = Regime(
            id=0,  # sera ignoré / remplacé par le repo
            nom=nom,
            desc=desc,

            min_rp_annuels=(
                min_rp_annuels
                if min_rp_annuels is not None
                else Regime.DEFAULT_MIN_RP_ANNUELS
            ),
            min_rp_dimanches=(
                min_rp_dimanches
                if min_rp_dimanches is not None
                else Regime.DEFAULT_MIN_RP_DIMANCHES
            ),

            min_rpsd=(
                min_rpsd
                if min_rpsd is not None
                else Regime.DEFAULT_MIN_RPSD
            ),
            min_rp_2plus=(
                min_rp_2plus
                if min_rp_2plus is not None
                else Regime.DEFAULT_MIN_RP_2PLUS
            ),

            min_rp_semestre=(
                min_rp_semestre
                if min_rp_semestre is not None
                else Regime.DEFAULT_MIN_RP_SEMESTRE
            ),

            avg_service_minutes=(
                avg_service_minutes
                if avg_service_minutes is not None
                else Regime.DEFAULT_AVG_SERVICE_MINUTES
            ),
            avg_tolerance_minutes=(
                avg_tolerance_minutes
                if avg_tolerance_minutes is not None
                else Regime.DEFAULT_AVG_TOLERANCE_MINUTES
            ),
        )

        return self.regime_repo.create(regime)
    
    def delete(self, regime_id: int) -> bool:
        regime = self.regime_repo.get_by_id(regime_id)
        if not regime:
            return False

        if self.agent_repo is not None and self.agent_repo.exists_for_regime(regime_id):
            raise ValueError("Cannot delete regime: regime is used by agents")

        return self.regime_repo.delete(regime_id)

    def get_by_id(self, regime_id: int) -> Regime | None:
        return self.regime_repo.get_by_id(regime_id)

    def list(self, *, limit: Optional[int] = None, offset: int = 0) -> List[Regime]:
        return self.regime_repo.list(limit=limit, offset=offset)

    def list_all(self) -> List[Regime]:
        return self.regime_repo.list_all()
    
    def update(self, regime_id: int, **changes: Any) -> Optional[Regime]:
        regime = self.regime_repo.get_by_id(regime_id)
        if not regime:
            return None

        if "nom" in changes:
            regime.nom = changes["nom"]
        if "desc" in changes:
            regime.desc = changes["desc"]

        if "min_rp_annuels" in changes:
            regime.min_rp_annuels = changes["min_rp_annuels"]
        if "min_rp_dimanches" in changes:
            regime.min_rp_dimanches = changes["min_rp_dimanches"]

        if "min_rpsd" in changes:
            regime.min_rpsd = changes["min_rpsd"]
        if "min_rp_2plus" in changes:
            regime.min_rp_2plus = changes["min_rp_2plus"]

        if "min_rp_semestre" in changes:
            regime.min_rp_semestre = changes["min_rp_semestre"]

        if "avg_service_minutes" in changes:
            regime.avg_service_minutes = changes["avg_service_minutes"]
        if "avg_tolerance_minutes" in changes:
            regime.avg_tolerance_minutes = changes["avg_tolerance_minutes"]

        return self.regime_repo.update(regime)

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