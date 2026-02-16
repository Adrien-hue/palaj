from __future__ import annotations

from datetime import date
from typing import List, Literal

from pydantic import BaseModel

from backend.app.dto.rh.rh_risk_level import RiskLevel

Severity = Literal["info", "warning", "error"]


class RhTriggerCountDTO(BaseModel):
    key: str
    severity: Severity
    count: int


class RhPosteDaySummaryDTO(BaseModel):
    date: date
    risk: RiskLevel

    agents_with_issues_count: int
    agents_with_blockers_count: int

    top_triggers: List[RhTriggerCountDTO] = []


class RhValidationPosteSummaryDTO(BaseModel):
    poste_id: int
    date_debut: date
    date_fin: date
    profile: str
    eligible_agents_count: int
    days: List[RhPosteDaySummaryDTO]
