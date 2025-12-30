from datetime import date
from typing import List, Optional
from pydantic import BaseModel

from backend.app.dto.tranches import TrancheDTO

class AgentDayDTO(BaseModel):
    date: date
    day_type: str
    description: Optional[str] = None
    shifts: List[TrancheDTO] = []
    is_off_shift: bool = False