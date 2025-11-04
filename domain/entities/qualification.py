from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import date
from typing import List, Optional

if TYPE_CHECKING:
    from core.domain.entities import Agent, Poste

    from db.repositories.agent_repo import AgentRepository
    from db.repositories.poste_repo import PosteRepository

class Qualification:
    """
    Représente la qualification d'un agent pour un poste donné.
    L'identifiant unique est composé de (agent_id, poste_id).
    Optionnellement, une date de qualification peut être enregistrée.
    """
    def __init__(self, agent_id: int, poste_id: int, date_qualification: Optional[date] =None):
        self.agent_id = agent_id
        self.poste_id = poste_id
        self.date_qualification = date_qualification
        
        self.id = f"{self.agent_id}_{self.poste_id}"

        self._agent: Agent | None = None
        self._poste: Poste | None = None

    # --- Debug & affichage ---
    def __repr__(self):
        date_str = self.date_qualification.isoformat() if self.date_qualification else "?"
        return f"<Qualification agent={self.agent_id} poste={self.poste_id} date={date_str}>"

    def __str__(self):
        return f"Qualification(agent={self.agent_id}, poste={self.poste_id})"

    def get_agent(self, agent_repo: AgentRepository):
        if self._agent is None:
            self._agent = agent_repo.get(self.agent_id)
        return self._agent

    def get_poste(self, poste_repo: PosteRepository):
        if self._poste is None:
            self._poste = poste_repo.get(self.poste_id)
        return self._poste

    # --- JSON helpers ---
    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "poste_id": self.poste_id,
            "date_qualification": self.date_qualification.isoformat() if self.date_qualification else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        date_val = data.get("date_qualification")
        parsed_date = date.fromisoformat(date_val) if date_val else None
        return cls(
            agent_id=data["agent_id"],
            poste_id=data["poste_id"],
            date_qualification=parsed_date
        )