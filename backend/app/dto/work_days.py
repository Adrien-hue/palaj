from pydantic import BaseModel

from datetime import date
from typing import List, Optional

from backend.app.dto.etats_jours_agents import EtatJourAgentDTO
from backend.app.dto.tranches import TrancheDTO

class WorkDayDTO(BaseModel):
    jour: date
    etat: Optional[EtatJourAgentDTO] = None
    tranches: List[TrancheDTO] = []