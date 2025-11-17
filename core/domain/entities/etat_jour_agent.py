from __future__ import annotations
from datetime import date
from enum import Enum
from typing import Optional

from core.domain.entities import Agent

class TypeJour(str, Enum):
    ABSENCE = "absence"
    CONGE = "conge"
    POSTE = "poste"
    REPOS = "repos"
    ZCOT = "zcot"

class EtatJourAgent:
    """
    Représente l'état d'un agent pour une journée donnée :
    - poste : l'agent travaille sur une ou plusieurs tranches
    - zcot    : l'agent est présent sur site en ZCOT
    - repos   : journée de repos
    - conge   : congé posé
    - absence : absence non prévue (maladie, etc.)
    """

    def __init__(
        self,
        agent_id: int,
        jour: date,
        type_jour: TypeJour,
        description: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.jour = jour
        self.type_jour: TypeJour = type_jour
        self.description = description or ""

        self._agent: Agent | None = None

    def __repr__(self):
        return f"<EtatJourAgent {self.agent_id} {self.jour.isoformat()} [{self.type_jour}]>"

    def __str__(self):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GRAY = "\033[90m"
        YELLOW = "\033[93m"

        return (
            f"{BOLD}{CYAN}État Jour Agent{RESET}\n"
            f"  {GRAY}Agent ID:{RESET} {self.agent_id}\n"
            f"  {GRAY}Jour:{RESET} {self.jour.isoformat()}\n"
            f"  {GRAY}Type:{RESET} {YELLOW}{self.type_jour}{RESET}\n"
            f"  {GRAY}Description:{RESET} {self.description or '—'}\n"
        )
    
    # Getters / Setters
    @property
    def agent(self) -> Agent | None:
        return self._agent

    def set_agent(self, agent: Agent | None) -> None:
        self._agent = agent

    # --- JSON helpers ---
    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "jour": self.jour.isoformat(),
            "type_jour": self.type_jour.value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EtatJourAgent:
        jour_val = date.fromisoformat(data["jour"])
        
        type_jour_str = data["type_jour"]

        try:
            type_jour_enum = TypeJour(type_jour_str)
        except ValueError:
            print(data)
            raise ValueError(f"TypeJour inconnu dans les données : {type_jour_str}")
        
        return cls(
            agent_id=data["agent_id"],
            jour=jour_val,
            type_jour=type_jour_enum,
            description=data.get("description"),
        )
