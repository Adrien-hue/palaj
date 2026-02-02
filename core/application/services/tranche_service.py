# core/application/services/tranche_service.py
from datetime import time
from typing import Any, List, Optional

from core.application.ports import (
    PosteRepositoryPort,
    TrancheRepositoryPort,
    AgentDayAssignmentRepositoryPort,
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
        agent_day_assignment_repo: AgentDayAssignmentRepositoryPort,
    ):
        self.poste_repo = poste_repo
        self.tranche_repo = tranche_repo
        self.agent_day_assignment_repo = agent_day_assignment_repo

    def count(self) -> int:
        return self.tranche_repo.count()
    
    def create(self, *, nom: str, heure_debut: time, heure_fin: time, poste_id: int, color: Optional[str] = None) -> Tranche:
        # Vérifier que le poste existe (si dispo)
        if self.poste_repo is not None:
            if self.poste_repo.get_by_id(poste_id) is None:
                raise ValueError("Poste not found")

        tranche = Tranche(
            id=0,
            nom=nom,
            heure_debut=heure_debut,
            heure_fin=heure_fin,
            poste_id=poste_id,
            color=color
        )
        return self.tranche_repo.create(tranche)

    def delete(self, tranche_id: int) -> bool:
        tranche = self.tranche_repo.get_by_id(tranche_id)
        if tranche is None:
            return False

        if self.agent_day_assignment_repo.exists_for_tranche(tranche_id):
            raise ValueError("Cannot delete tranche: tranche is used in agent_day_assignments")

        return self.tranche_repo.delete(tranche_id)

    def get_by_id(self, tranche_id: int) -> Tranche | None:
        return self.tranche_repo.get_by_id(tranche_id)

    def list(self, *, limit: Optional[int] = None, offset: int = 0) -> List[Tranche]:
        return self.tranche_repo.list(limit=limit, offset=offset)

    def list_all(self) -> List[Tranche]:
        return self.tranche_repo.list_all()
    
    def list_by_poste_id(self, poste_id: int) -> List[Tranche]:
        return self.tranche_repo.list_by_poste_id(poste_id)

    def update(self, tranche_id: int, **changes: Any) -> Optional[Tranche]:
        tranche = self.tranche_repo.get_by_id(tranche_id)
        if not tranche:
            return None

        # vérif poste si changement
        if "poste_id" in changes and self.poste_repo is not None:
            if self.poste_repo.get_by_id(changes["poste_id"]) is None:
                raise ValueError("Poste not found")

        # applique changements
        if "nom" in changes:
            tranche.nom = changes["nom"]
        if "heure_debut" in changes:
            tranche.heure_debut = changes["heure_debut"]
        if "heure_fin" in changes:
            tranche.heure_fin = changes["heure_fin"]
        if "poste_id" in changes:
            tranche.poste_id = changes["poste_id"]
        if "color" in changes:
            tranche.color = changes["color"]

        return self.tranche_repo.update(tranche)


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