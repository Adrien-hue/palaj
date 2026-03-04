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
    quality_profile: str = Field(default="balanced")
    v3_strategy: str = Field(default="two_phase_lns")
    phase1_fraction: float | None = Field(default=None, gt=0, le=1)
    phase1_seconds: float | None = Field(default=None, gt=0)
    lns_iter_seconds: float | None = Field(default=None, gt=0)
    lns_min_remaining_seconds: float | None = Field(default=None, ge=0)
    lns_strict_improve: bool = Field(default=True)
    lns_max_days_to_relax: int | None = Field(default=None, ge=1)
    lns_neighborhood_mode: str = Field(default="poste_only")
    min_lns_seconds: float | None = Field(default=None, ge=0)
    phase2_max_fraction_of_remaining: float | None = Field(default=None, gt=0, le=1)
    phase2_no_improve_seconds: float | None = Field(default=None, ge=0)
    enable_decision_strategy: bool | None = Field(default=None)
    enable_symmetry_breaking: bool | None = Field(default=None)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date, info):
        start_date = info.data.get("start_date")
        if start_date and start_date > end_date:
            raise ValueError("start_date must be <= end_date")
        return end_date

    @field_validator("quality_profile")
    @classmethod
    def validate_quality_profile(cls, value: str) -> str:
        allowed = {"fast", "balanced", "high"}
        if value not in allowed:
            raise ValueError(f"quality_profile must be one of {sorted(allowed)}")
        return value

    @field_validator("lns_neighborhood_mode")
    @classmethod
    def validate_lns_neighborhood_mode(cls, value: str) -> str:
        allowed = {"poste_only", "poste_plus_one", "top_days_global", "poste_plus_one_top_days", "mixed"}
        if value not in allowed:
            raise ValueError(f"lns_neighborhood_mode must be one of {sorted(allowed)}")
        return value

    @field_validator("v3_strategy")
    @classmethod
    def validate_v3_strategy(cls, value: str) -> str:
        allowed = {"two_phase", "two_phase_lns", "lns_only"}
        if value not in allowed:
            raise ValueError(f"v3_strategy must be one of {sorted(allowed)}")
        return value


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
