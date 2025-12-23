# core/application/services/poste_service.py
from typing import List, Optional

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

    def count(self) -> int:
        return self.poste_repo.count()

    def get_by_id(self, poste_id: int) -> Poste | None:
        return self.poste_repo.get_by_id(poste_id)

    def list(self, *, limit: Optional[int] = None, offset: int = 0) -> List[Poste]:
        return self.poste_repo.list(limit=limit, offset=offset)

    def list_all(self) -> List[Poste]:
        return self.poste_repo.list_all()

    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_poste_complet(self, poste_id: int) -> Poste | None:
        poste = self.poste_repo.get_by_id(poste_id)
        if not poste:
            return None

        return self._enrich_poste(poste)

    def list_postes_complets(
        self, *, limit: Optional[int] = None, offset: int = 0
    ) -> List[Poste]:
        postes = self.poste_repo.list(limit=limit, offset=offset)
    
        return [self._enrich_poste(poste) for poste in postes]
    
    def _enrich_poste(self, poste: Poste) -> Poste:
        poste.set_tranches(self.tranche_repo.list_by_poste_id(poste.id))
        poste.set_qualifications(self.qualification_repo.list_for_poste(poste.id))
        return poste