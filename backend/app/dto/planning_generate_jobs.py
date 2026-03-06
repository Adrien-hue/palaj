from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from core.domain.enums.planning_draft_status import PlanningDraftStatus


class PlanningGenerateJobListItem(BaseModel):
    job_id: UUID
    draft_id: int
    team_id: int
    team_name: str | None = None
    start_date: date
    end_date: date
    status: PlanningDraftStatus
    progress: float = Field(ge=0, le=1)
    created_at: datetime
    # Kept nullable for robustness with historical rows if DB contains nulls.
    updated_at: datetime | None = None


class PlanningGenerateJobsListResponse(BaseModel):
    items: list[PlanningGenerateJobListItem]
    page: int
    page_size: int
    total: int
