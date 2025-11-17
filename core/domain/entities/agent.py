from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from core.domain.entities import Affectation, EtatJourAgent, Qualification, Regime

class Agent:
    """
    Entité métier représentant un agent.
    Entièrement indépendante de la base de données ou des repositories.
    """

    def __init__(
        self,
        id: int,
        nom: str,
        prenom: str,
        code_personnel: str = "",
        regime_id: Optional[int] = None,
    ):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.code_personnel = code_personnel

        self.regime_id = regime_id
        self._regime: Optional[Regime] = None
        self._qualifications: Optional[List[Qualification]] = None
        self._affectations: Optional[List[Affectation]] = None

        self._etat_jours: Optional[List[EtatJourAgent]] = None

    def __repr__(self):
        return (
            f"<Agent id={self.id}, nom='{self.nom}', prenom='{self.prenom}', "
            f"code='{self.code_personnel}', regime_id={self.regime_id}>"
        )

    def __str__(self):
        RESET, BOLD, CYAN, YELLOW, GRAY, GREEN = "\033[0m", "\033[1m", "\033[96m", "\033[93m", "\033[90m", "\033[92m"
        regime_str = f"{YELLOW}{self._regime.nom}{RESET}" if self._regime else f"{GRAY}Aucun{RESET}"

        qual_count = len(self._qualifications or [])
        affect_count = len(self._affectations or [])
        etat_count = len(self._etat_jours or [])

        return (
            f"{BOLD}{CYAN}Agent{RESET} {self.prenom} {self.nom}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Code personnel:{RESET} {self.code_personnel or 'Non défini'}\n"
            f"  {GRAY}Régime:{RESET} {regime_str}\n"
            f"  {GRAY}Qualifications:{RESET} {GREEN}{qual_count}{RESET}\n"
            f"  {GRAY}Affectations:{RESET} {affect_count}\n"
            f"  {GRAY}États journaliers:{RESET} {etat_count}\n"
        )

    # Getters / Setters

    @property
    def affectations(self) -> List["Affectation"]:
        return self._affectations or []

    def set_affectations(self, affectations: List["Affectation"]) -> None:
        self._affectations = affectations

    @property
    def etat_jours(self) -> List["EtatJourAgent"]:
        return self._etat_jours or []

    def set_etat_jours(self, etats: List["EtatJourAgent"]) -> None:
        self._etat_jours = etats

    @property
    def qualifications(self) -> List["Qualification"]:
        return self._qualifications or []

    def set_qualifications(self, qualifications: List["Qualification"]) -> None:
        self._qualifications = qualifications

    @property
    def regime(self) -> Optional["Regime"]:
        return self._regime

    def set_regime(self, regime: Optional["Regime"]) -> None:
        self._regime = regime

    # Méthodes publiques

    def get_full_name(self) -> str:
        return f"{self.prenom} {self.nom}"

    def to_dict(self) -> Dict[str, Any]:
        """Conversion légère en dict (sans les sous-objets)."""
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "code_personnel": self.code_personnel,
            "regime_id": self.regime_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Reconstruction d'un agent à partir d'un dict brut."""
        return cls(
            id=data["id"],
            nom=data["nom"],
            prenom=data["prenom"],
            code_personnel=data.get("code_personnel", ""),
            regime_id=data.get("regime_id"),
        )