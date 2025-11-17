from typing import List
from core.domain.entities.tranche import Tranche


class TrancheService:
    """
    Service applicatif : coordination entre BDD, enrichissement et validation métier.
    - Charge les tranches et leur poste associé
    - Délègue la validation métier au domaine
    """

    def __init__(self, tranche_repo, poste_repo):
        self.tranche_repo = tranche_repo
        self.poste_repo = poste_repo

    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_tranche_complet(self, tranche_id: int) -> Tranche | None:
        """Récupère une tranche unique avec son poste associé."""
        tranche = self.tranche_repo.get(tranche_id)
        
        if not tranche:
            return None
        
        tranche.set_poste(self.poste_repo.get(tranche.poste_id))
        
        return tranche

    def list_tranches_complets(self) -> List[Tranche]:
        """Retourne toutes les tranches avec leur poste associé."""
        tranches = self.tranche_repo.list_all()
        for t in tranches:
            t.set_poste(self.poste_repo.get(t.poste_id))
        return tranches