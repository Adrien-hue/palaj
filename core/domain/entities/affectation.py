from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date

if TYPE_CHECKING:
    from core.domain.entities import Agent, Tranche

    from db.repositories.agent_repo import AgentRepository
    from db.repositories.tranche_repo import TrancheRepository

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

        # ID composé
        self.id = f"{agent_id}_{jour.strftime('%Y%m%d')}_{tranche_id}"

        # Lazy loading
        self._agent: Agent | None = None
        self._tranche: Tranche | None = None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Affectation) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"<Affectation agent={self.agent_id}, tranche={self.tranche_id}, jour={self.jour.isoformat()}>"

    def __str__(self) -> str:
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GRAY = "\033[90m"

        return (
            f"{BOLD}{CYAN}Affectation{RESET}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Agent ID:{RESET} {self.agent_id}\n"
            f"  {GRAY}Tranche ID:{RESET} {self.tranche_id}\n"
            f"  {GRAY}Jour:{RESET} {self.jour.isoformat()}\n"
        )

    # --- Lazy loading ---
    def get_agent(self, agent_repo: AgentRepository):
        if self._agent is None:
            self._agent = agent_repo.get(self.agent_id)
        return self._agent

    def get_tranche(self, tranche_repo: TrancheRepository):
        if self._tranche is None:
            self._tranche = tranche_repo.get(self.tranche_id)
        return self._tranche

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
