# core/application/services/tranche_service.py
from typing import List

from core.application.ports import (
    PosteRepositoryPort,
    TrancheRepositoryPort,
)
from core.domain.entities import Tranche


class TrancheService:
    """
    Service applicatif : coordination entre BDD, enrichissement et validation métier.
    - Charge les tranches et leur poste associé
    - Délègue la validation métier au domaine
    """

    def __init__(
        self,
        poste_repo: PosteRepositoryPort,
        tranche_repo: TrancheRepositoryPort,
    ):
        self.poste_repo = poste_repo
        self.tranche_repo = tranche_repo

    def list_all(self) -> List[Tranche]:
        return self.tranche_repo.list_all()
    
    def get_by_id(self, tranche_id: int) -> Tranche | None:
        return self.tranche_repo.get_by_id(tranche_id)
    
    def list_by_poste_id(self, poste_id: int) -> List[Tranche]:
        return self.tranche_repo.list_by_poste_id(poste_id)

    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_tranche_complet(self, tranche_id: int) -> Tranche | None:
        """Récupère une tranche unique avec son poste associé."""
        tranche = self.tranche_repo.get_by_id(tranche_id)
        
        if not tranche:
            return None
        
        tranche.set_poste(self.poste_repo.get_by_id(tranche.poste_id))
        
        return tranche

    def list_tranches_complets(self) -> List[Tranche]:
        """Retourne toutes les tranches avec leur poste associé."""
        tranches = self.tranche_repo.list_all()
        for t in tranches:
            t.set_poste(self.poste_repo.get_by_id(t.poste_id))
        return tranches