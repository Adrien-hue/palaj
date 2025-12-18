# core/application/services/poste_service.py
from typing import List

from core.application.ports import (
    PosteRepositoryPort,
    QualificationRepositoryPort,
    TrancheRepositoryPort,
)
from core.domain.entities import Poste


class PosteService:
    """
    Service applicatif : coordonne les repositories et le validateur métier.
    """

    def __init__(
        self,
        poste_repo: PosteRepositoryPort,
        qualification_repo: QualificationRepositoryPort,
        tranche_repo: TrancheRepositoryPort,
    ):
        self.poste_repo = poste_repo
        self.qualification_repo = qualification_repo
        self.tranche_repo = tranche_repo

    def get_by_id(self, poste_id: int) -> Poste | None:
        return self.poste_repo.get_by_id(poste_id)
    
    def list_all(self) -> List[Poste]:
        return self.poste_repo.list_all()

    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_poste_complet(self, poste_id: int) -> Poste | None:
        poste = self.poste_repo.get_by_id(poste_id)
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