from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.year_rule import YearRule
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity


class RegimeCReposRule(YearRule):
    """
    Regime C (regime_id = 2)

    Full civil year requirements:
    - At least 118 periodic rest days (RP)
    - Including at least 52 Sundays of rest

    Partial year:
    - INFO only (no blocking controls)
    """

    name = "RegimeCReposRule"
    description = "Repos annuels spécifiques au régime C (118 RP / 52 dimanches)."

    MIN_RP_ANNUELS = 118
    MIN_RP_DIMANCHES = 52

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    # ---------------------------------------------------------
    # Applicability
    # ---------------------------------------------------------
    def applies_to(self, context: PlanningContext) -> bool:
        regime_id = getattr(context.agent, "regime_id", None)
        return regime_id == 2

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        if not self.applies_to(context):
            return True, []
        return super().check(context)

    # ---------------------------------------------------------
    # Year logic
    # ---------------------------------------------------------
    def check_year(
        self,
        context: PlanningContext,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        # No data for this year
        if not work_days:
            v = self.info_v(
                code="REGIME_C_EMPTY_YEAR",
                msg=f"[{year}] Aucun jour planifié pour cet agent en régime C.",
                start_date=year_start,
                end_date=year_end,
                meta={"year": year, "is_full": is_full, "regime_id": 2},
            )
            return True, [to_domain_alert(v)]

        # Canonical RH input
        rh_days = [rh_day_from_workday(context.agent.id, wd) for wd in work_days]
        rh_days.sort(key=lambda d: d.day_date)

        # RH-first summary
        repos_summary = self.analyzer.summarize_rh_days(rh_days)

        # Always add a synthesis line
        summary_msg = (
            f"[{year}] Régime C - Repos périodiques détectés : "
            f"{repos_summary.total_rest_days} RP au total, "
            f"dont {repos_summary.total_rest_sundays} dimanches. "
            f"Minima annuels attendus : "
            f"{self.MIN_RP_ANNUELS} RP / {self.MIN_RP_DIMANCHES} dimanches."
        )
        alerts.append(
            to_domain_alert(
                self.info_v(
                    code="REGIME_C_REPOS_SYNTHESIS",
                    msg=summary_msg,
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "is_full": is_full,
                        "regime_id": 2,
                        "total_rest_days": repos_summary.total_rest_days,
                        "total_rest_sundays": repos_summary.total_rest_sundays,
                        "min_rp_days": self.MIN_RP_ANNUELS,
                        "min_rp_sundays": self.MIN_RP_DIMANCHES,
                    },
                )
            )
        )

        # Partial year: info only
        if not is_full:
            v = self.info_v(
                code="REGIME_C_REPOS_PARTIAL_YEAR",
                msg=(
                    f"[{year}] Période incomplète : les minima annuels pour le régime C "
                    "ne sont pas contrôlés de manière stricte sur une portion d'année."
                ),
                start_date=year_start,
                end_date=year_end,
                meta={"year": year, "regime_id": 2},
            )
            alerts.append(to_domain_alert(v))
            return True, alerts

        # Full year: strict controls
        if repos_summary.total_rest_days < self.MIN_RP_ANNUELS:
            v = self.error_v(
                code="REGIME_C_REPOS_RP_INSUFFISANTS",
                msg=(
                    f"[{year}] Repos périodiques insuffisants pour le régime C : "
                    f"{repos_summary.total_rest_days}/{self.MIN_RP_ANNUELS} jours sur l'année."
                ),
                start_date=year_start,
                end_date=year_end,
                meta={
                    "year": year,
                    "regime_id": 2,
                    "total_rest_days": repos_summary.total_rest_days,
                    "min_required": self.MIN_RP_ANNUELS,
                },
            )
            alerts.append(to_domain_alert(v))

        if repos_summary.total_rest_sundays < self.MIN_RP_DIMANCHES:
            v = self.error_v(
                code="REGIME_C_REPOS_DIMANCHES_INSUFFISANTS",
                msg=(
                    f"[{year}] Dimanches de repos insuffisants pour le régime C : "
                    f"{repos_summary.total_rest_sundays}/{self.MIN_RP_DIMANCHES} dimanches sur l'année."
                ),
                start_date=year_start,
                end_date=year_end,
                meta={
                    "year": year,
                    "regime_id": 2,
                    "total_rest_sundays": repos_summary.total_rest_sundays,
                    "min_required": self.MIN_RP_DIMANCHES,
                },
            )
            alerts.append(to_domain_alert(v))

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
