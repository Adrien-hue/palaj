# backend/app/mappers/rh_validation_poste_summary.py
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Iterable, List, Tuple

from backend.app.dto.rh.rh_validation_summary import (
    RhPosteDaySummaryDTO,
    RhTriggerCountDTO,
    RhValidationPosteSummaryDTO,
    RiskLevel,
)

from core.rh_rules.models.rule_result import RuleResult
from core.utils.severity import Severity


HIGHLIGHT_RULES = {
    "ReposQuotidienRule",
    "ReposDoubleRule",
    "GrandePeriodeTravailRule",
    "DureeTravailRule",
    "AmplitudeMaxRule",
}


def _iter_dates(start: date, end: date) -> Iterable[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _severity_to_str(sev: Severity) -> str:
    if sev == Severity.ERROR:
        return "error"
    if sev == Severity.WARNING:
        return "warning"
    return "info"


def _violation_intersects_day(v, day: date) -> bool:
    if v.start_date is None or v.end_date is None:
        return False
    return v.start_date <= day <= v.end_date

def _risk_from_agent_counts(blockers_count: int, issues_count: int) -> RiskLevel:
    if blockers_count > 0:
        return RiskLevel.HIGH
    if issues_count > 0:
        return RiskLevel.MEDIUM
    return RiskLevel.NONE

def to_poste_summary_dto(
    *,
    poste_id: int,
    start: date,
    end: date,
    profile,
    qualified_agent_ids: List[int],
    per_agent_results: List[Tuple[int, RuleResult]],
) -> RhValidationPosteSummaryDTO:
    # day -> nb agents ayant au moins un WARNING/ERROR sur règles highlight
    day_agents_with_issues = Counter()

    # day -> nb agents ayant au moins un ERROR sur règles highlight
    day_agents_with_blockers = Counter()

    # day -> (rule_name, severity) -> count (WARNING/ERROR only)
    day_triggers = defaultdict(Counter)

    for agent_id, result in per_agent_results:
        for day in _iter_dates(start, end):
            violations_for_day = [
                v for v in result.violations
                if _violation_intersects_day(v, day)
                and v.rule_name in HIGHLIGHT_RULES
                and v.severity != Severity.INFO
            ]

            if not violations_for_day:
                continue

            # flags agent-level pour ce jour
            has_issue = False
            has_blocker = False

            for v in violations_for_day:
                has_issue = True
                if v.severity == Severity.ERROR:
                    has_blocker = True

                sev_str = _severity_to_str(v.severity)
                day_triggers[day][(v.rule_name, sev_str)] += 1

            if has_issue:
                day_agents_with_issues[day] += 1
            if has_blocker:
                day_agents_with_blockers[day] += 1

    days_dto: List[RhPosteDaySummaryDTO] = []

    for day in _iter_dates(start, end):
        issues_count = int(day_agents_with_issues.get(day, 0))
        blockers_count = int(day_agents_with_blockers.get(day, 0))

        triggers_counter = day_triggers.get(day, Counter())
        top = triggers_counter.most_common(3)

        days_dto.append(
            RhPosteDaySummaryDTO(
                date=day,
                risk=_risk_from_agent_counts(blockers_count, issues_count),
                agents_with_issues_count=issues_count,
                agents_with_blockers_count=blockers_count,
                top_triggers=[
                    RhTriggerCountDTO(
                        key=rule_name,
                        severity=severity,
                        count=count,
                    )
                    for (rule_name, severity), count in top
                ],
            )
        )

    return RhValidationPosteSummaryDTO(
        poste_id=poste_id,
        date_debut=start,
        date_fin=end,
        profile=getattr(profile, "value", str(profile)),
        eligible_agents_count=len(qualified_agent_ids),
        days=days_dto,
    )