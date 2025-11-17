from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date

if TYPE_CHECKING:
    from core.domain.entities import Agent, Tranche

class Affectation:
    """
    Lien entre un agent, une tranche et un jour de travail.
    """

    def __init__(self, agent_id: int, tranche_id: int, jour: date):
        if not isinstance(jour, date):
            raise TypeError("jour doit être une instance de datetime.date")

        self.agent_id = agent_id
        self.tranche_id = tranche_id
        self.jour = jour

        self._agent: Agent | None = None
        self._tranche: Tranche | None = None

    def __repr__(self) -> str:
        return f"<Affectation agent={self.agent_id}, tranche={self.tranche_id}, jour={self.jour.isoformat()}>"

    def __str__(self) -> str:
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GRAY = "\033[90m"

        return (
            f"{BOLD}{CYAN}Affectation{RESET}\n"
            f"  {GRAY}Agent ID:{RESET} {self.agent_id}\n"
            f"  {GRAY}Tranche ID:{RESET} {self.tranche_id}\n"
            f"  {GRAY}Jour:{RESET} {self.jour.isoformat()}\n"
        )

    # Getters / Setters
    @property
    def agent(self) -> Agent | None:
        return self._agent
    
    def set_agent(self, agent: Optional[Agent]) -> None:
        self._agent = agent
    
    @property
    def tranche(self) -> Tranche | None:
        return self._tranche
    
    def set_tranche(self, tranche: Optional[Tranche]) -> None:
        self._tranche = tranche

    # --- JSON helpers ---
    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "tranche_id": self.tranche_id,
            "jour": self.jour.strftime("%Y-%m-%d"),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Affectation:
        jour = date.fromisoformat(data["jour"])
        return cls(
            agent_id=data["agent_id"],
            tranche_id=data["tranche_id"],
            jour=jour
        )
