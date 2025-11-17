# core/application/services/poste_service.py
from typing import List
from core.domain.entities.poste import Poste


class PosteService:
    """
    Service applicatif : coordonne les repositories et le validateur métier.
    """

    def __init__(self, poste_repo, tranche_repo, qualification_repo):
        self.poste_repo = poste_repo
        self.tranche_repo = tranche_repo
        self.qualification_repo = qualification_repo

    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_poste_complet(self, poste_id: int) -> Poste | None:
        poste = self.poste_repo.get(poste_id)
        if not poste:
            return None

        poste.set_tranches(self.tranche_repo.list_by_poste_id(poste.id))
        poste.set_qualifications(self.qualification_repo.list_for_poste(poste.id))
        return poste

    def list_postes_complets(self) -> List[Poste]:
        postes = self.poste_repo.list_all()
        for p in postes:
            p.set_tranches(self.tranche_repo.list_by_poste_id(p.id))
            p.set_qualifications(self.qualification_repo.list_for_poste(p.id))
        return postes