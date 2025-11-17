from __future__ import annotations
from typing import TYPE_CHECKING

from typing import List

if TYPE_CHECKING:
    from core.domain.entities import Qualification, Tranche

class Poste:
    def __init__(self, id: int, nom: str):
        """
        Représente un poste à couvrir dans le planning.

        :param id: Identifiant unique du poste
        :param nom: Nom du poste (ex: 'GM J', 'RLIV6P')
        """
        self.id = id
        self.nom = nom

        self._qualifications: List[Qualification] | None = None
        self._tranches: List[Tranche] | None = None

    def __repr__(self):
        return f"<Poste {self.nom}>"

    def __str__(self):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        BLUE = "\033[94m"
        GRAY = "\033[90m"


        qual_count = len(self._qualifications) if self._qualifications is not None else "Non chargé"

        return (
            f"{BOLD}{BLUE}Poste {self.nom}{RESET}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Qualifications:{RESET} {qual_count}\n"

        )
    
    # Getters / Setters
    @property
    def qualifications(self):
        return getattr(self, "_qualifications", [])
    
    def set_qualifications(self, qualifications):
        """Injecte les qualifications depuis le domaine service."""
        self._qualifications = qualifications
    
    @property
    def tranches(self):
        return getattr(self, "_tranches", [])

    def set_tranches(self, tranches):
        """Injecte les tranches depuis le domaine service."""
        self._tranches = tranches

    def to_dict(self) -> dict:
        """
        Sérialisation JSON-friendly du poste.
        """
        return {
            "id": self.id,
            "nom": self.nom,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            nom=data["nom"],
        )