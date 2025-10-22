from __future__ import annotations
from typing import TYPE_CHECKING

from typing import Any, Dict, List, Optional

if TYPE_CHECKING:
    from models.qualification import Qualification
    from models.regime import Regime
    from models.etat_jour_agent import EtatJourAgent

    from db.repositories.qualification_repo import QualificationRepository
    from db.repositories.regime_repo import RegimeRepository
    from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository

class Agent:
    def __init__(self, id: int, nom: str, prenom: str, code_personnel: str = "", regime_id: Optional[int] = None):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.code_personnel = code_personnel
        
        self.regime_id = regime_id
        self._regime: Regime | None = None

        self._qualifications: List[Qualification] | None = None

        # États journaliers
        self._zcot_jours: List[EtatJourAgent] | None = None
        self._repos_jours: List[EtatJourAgent] | None = None
        self._absences_jours: List[EtatJourAgent] | None = None
        self._conges_jours: List[EtatJourAgent] | None = None
        self._travail_jours: List[EtatJourAgent] | None = None

    def __repr__(self):
        return (
            f"<Agent id={self.id}, nom='{self.nom}', prenom='{self.prenom}', "
            f"code='{self.code_personnel}', regime_id={self.regime_id}>"
        )

    def __str__(self):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        YELLOW = "\033[93m"
        GRAY = "\033[90m"
        GREEN = "\033[92m"

        regime_str = f"{YELLOW}{self.regime_id}{RESET}" if self.regime_id else f"{GRAY}Aucun{RESET}"
        qual_count = len(self._qualifications) if self._qualifications is not None else "Non chargé"
        absences_count = len(self._absences_jours) if self._absences_jours is not None else "Non chargé"
        conges_count = len(self._conges_jours) if self._conges_jours is not None else "Non chargé"
        repos_count = len(self._repos_jours) if self._repos_jours is not None else "Non chargé"
        zcot_count = len(self._zcot_jours) if self._zcot_jours is not None else "Non chargé"
        travail_count = len(self._travail_jours) if self._travail_jours is not None else "Non chargé"
    
        return (
            f"{BOLD}{CYAN}Agent{RESET} {self.prenom} {self.nom}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Code personnel:{RESET} {self.code_personnel or 'Non défini'}\n"
            f"  {GRAY}Régime ID:{RESET} {regime_str}\n"
            f"  {GRAY}Qualifications:{RESET} {GREEN}{qual_count}{RESET}\n"
            f"  {GRAY}Absences:{RESET} {absences_count}\n"
            f"  {GRAY}Congés:{RESET} {conges_count}\n"
            f"  {GRAY}Repos:{RESET} {repos_count}\n"
            f"  {GRAY}ZCOT:{RESET} {zcot_count}\n"
            f"  {GRAY}En poste:{RESET} {travail_count}\n"
        )
    
    @property
    def qualifications(self):
        return getattr(self, "_qualifications", [])

    @property
    def regime(self):
        return self._regime
    
    def get_qualifications(self, qualification_repo: QualificationRepository):
        if self._qualifications is None:
            self._qualifications = qualification_repo.list_for_agent(self.id)
        return self._qualifications

    def get_regime(self, regime_repo: RegimeRepository):
        """Récupère l'objet Regime associé à l'agent, avec lazy loading."""
        if self.regime_id is None:
            return None
        if self._regime is None:
            self._regime = regime_repo.get(self.regime_id)
        return self._regime

    def get_zcot_jours(self, etat_repo: EtatJourAgentRepository) -> List[EtatJourAgent]:
        if self._zcot_jours is None:
            self._zcot_jours = etat_repo.list_zcot_for_agent(self.id)
        return self._zcot_jours

    def get_repos_jours(self, etat_repo: EtatJourAgentRepository) -> List[EtatJourAgent]:
        if self._repos_jours is None:
            self._repos_jours = etat_repo.list_repos_for_agent(self.id)
        return self._repos_jours

    def get_absences_jours(self, etat_repo: EtatJourAgentRepository) -> List[EtatJourAgent]:
        if self._absences_jours is None:
            self._absences_jours = etat_repo.list_absences_for_agent(self.id)
        return self._absences_jours

    def get_conges_jours(self, etat_repo: EtatJourAgentRepository) -> List[EtatJourAgent]:
        if self._conges_jours is None:
            self._conges_jours = etat_repo.list_conges_for_agent(self.id)
        return self._conges_jours

    def get_travail_jours(self, etat_repo: EtatJourAgentRepository) -> List[EtatJourAgent]:
        if self._travail_jours is None:
            self._travail_jours = etat_repo.list_travail_for_agent(self.id)
        return self._travail_jours

    def get_full_name(self):
        return f"{self.prenom} {self.nom}"

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'agent en dictionnaire JSON-sérialisable."""
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "code_personnel": self.code_personnel,
            "regime_id": self.regime_id if self.regime_id else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Crée une instance d'Agent depuis un dictionnaire JSON."""
        agent = cls(
            id=data["id"],
            nom=data["nom"],
            prenom=data["prenom"],
            code_personnel=data.get("code_personnel") or "",
            regime_id=data.get("regime_id") or None
        )
        # Les qualifications seront rechargées séparément si besoin
        return agent