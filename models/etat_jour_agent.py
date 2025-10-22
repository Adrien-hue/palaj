from __future__ import annotations
from datetime import date
from typing import Literal, Optional

TYPE_JOUR = Literal["poste", "zcot", "repos", "conge", "absence"]

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
        type_jour: TYPE_JOUR,
        description: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.jour = jour
        self.type_jour: TYPE_JOUR = type_jour
        self.description = description or ""

        self.id = f"{agent_id}_{jour.strftime('%Y%m%d')}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EtatJourAgent) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

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

    # --- JSON helpers ---
    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "jour": self.jour.isoformat(),
            "type_jour": self.type_jour,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EtatJourAgent:
        jour_val = date.fromisoformat(data["jour"])
        return cls(
            agent_id=data["agent_id"],
            jour=jour_val,
            type_jour=data["type_jour"],
            description=data.get("description"),
        )
