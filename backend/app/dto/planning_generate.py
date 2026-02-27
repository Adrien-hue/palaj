from __future__ import annotations

from datetime import date
from uuid import UUID
from typing import Any

from pydantic import BaseModel, Field, field_validator

from core.domain.enums.planning_draft_status import PlanningDraftStatus


class PlanningGenerateRequest(BaseModel):
    team_id: int
    start_date: date
    end_date: date
    seed: int | None = None
    time_limit_seconds: int = Field(default=60, ge=1)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date, info):
        start_date = info.data.get("start_date")
        if start_date and start_date > end_date:
            raise ValueError("start_date must be <= end_date")
        return end_date


class PlanningGenerateResponse(BaseModel):
    job_id: UUID
    draft_id: int
    status: PlanningDraftStatus


class PlanningGenerateStatusResponse(BaseModel):
    job_id: UUID
    draft_id: int
    status: PlanningDraftStatus
    progress: float = Field(ge=0, le=1)
    result_stats: dict[str, Any] | None = None
    error: str | None = None
