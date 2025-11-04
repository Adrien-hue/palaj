from __future__ import annotations
from typing import TYPE_CHECKING

from typing import List, Optional

if TYPE_CHECKING:
    from core.domain.entities import Qualification, Tranche

    from db.repositories.qualification_repo import QualificationRepository
    from db.repositories.tranche_repo import TrancheRepository

class Poste:
    def __init__(self, id: int, nom: str, tranche_ids: Optional[List[int]] = None):
        """
        Représente un poste à couvrir dans le planning.

        :param id: Identifiant unique du poste
        :param nom: Nom du poste (ex: 'GM J', 'RLIV6P')
        :param tranche_ids: Liste des identifiants des tranches associées
        """
        self.id = id
        self.nom = nom
        self.tranche_ids: List[int] = tranche_ids or []

        self._tranches: List[Tranche] | None = None

        self._qualifications: List[Qualification] | None = None

    def __repr__(self):
        return f"<Poste {self.nom}: {len(self.tranche_ids)} tranches>"

    def __str__(self):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        BLUE = "\033[94m"
        GRAY = "\033[90m"

        tranche_count = ", ".join(str(t.abbr) for t in self._tranches) if self._tranches is not None else "Non chargé"

        qual_count = len(self._qualifications) if self._qualifications is not None else "Non chargé"

        return (
            f"{BOLD}{BLUE}Poste {self.nom}{RESET}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Tranches ids:{RESET} {self.tranche_ids}\n"
            f"  {GRAY}Tranches chargées:{RESET} {tranche_count}\n"
            f"  {GRAY}Qualifications:{RESET} {qual_count}\n"

        )
    
    @property
    def qualifications(self):
        return getattr(self, "_qualifications", [])

    def get_tranches(self, tranche_repo: TrancheRepository):
        if self._tranches is None:
            list_tranche = []

            for id in self.tranche_ids:
                tranche = tranche_repo.get(id)

                if tranche:
                    list_tranche.append(tranche)

            self._tranches = list_tranche
        return self._tranches
    
    def get_qualifications(self, qualification_repo: QualificationRepository):
        if self._qualifications is None:
            self._qualifications = qualification_repo.list_for_poste(self.id)
        return self._qualifications

    def to_dict(self) -> dict:
        """
        Sérialisation JSON-friendly du poste.
        """
        return {
            "id": self.id,
            "nom": self.nom,
            "tranches": self.tranche_ids,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            nom=data["nom"],
            tranche_ids=data["tranches"]
        )