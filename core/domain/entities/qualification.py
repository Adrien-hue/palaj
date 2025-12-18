from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import date
from typing import Optional

if TYPE_CHECKING:
    from core.domain.entities import Agent, Poste

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

        self._agent: Agent | None = None
        self._poste: Poste | None = None

    # --- Debug & affichage ---
    def __repr__(self):
        date_str = self.date_qualification.isoformat() if self.date_qualification else "?"
        return f"<Qualification agent={self.agent_id} poste={self.poste_id} date={date_str}>"

    def __str__(self):
        return f"Qualification(agent={self.agent_id}, poste={self.poste_id})"

    # Getters / Setters
    @property
    def agent(self) -> Agent | None:
        return self._agent
    
    def set_agent(self, agent: Optional[Agent]) -> None:
        self._agent = agent
    
    @property
    def poste(self) -> Poste | None:
        return self._poste
    
    def set_poste(self, poste: Optional[Poste]) -> None:
        self._poste = poste

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