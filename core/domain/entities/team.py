from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class Team:
    id: Optional[int]
    name: str
    description: Optional[str]
    created_at: Optional[datetime]