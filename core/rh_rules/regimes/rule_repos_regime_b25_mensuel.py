from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.month_rule import MonthRule
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity


class RegimeB25ReposMensuelRule(MonthRule):
    """
    Regime B25 (regime_id = 1)

    For each FULL civil month:
      - At least 1 RPSD (Saturday->Sunday rest period)
      - At least 2 rest periods of >= 2 days total (including >=1 RPSD)

    Partial month:
      - INFO only (if at least one rest day exists)
    """

    name = "RegimeB25ReposMensuelRule"
    description = (
        "Contrôle mensuel des repos B25 : par mois complet, au moins 1 RPSD et "
        "au moins 2 périodes de repos de 2+ jours (dont ≥1 RPSD)."
    )

    MIN_RPSD = 1
    MIN_RP_2PLUS = 2

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    # ---------------------------------------------------------
    # Applicability
    # ---------------------------------------------------------
    def applies_to(self, context: PlanningContext) -> bool:
        regime_id = getattr(context.agent, "regime_id", None)
        return regime_id == 1

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        if not self.applies_to(context):
            return True, []
        if not context.work_days:
            return True, []
        return super().check(context)

    # ---------------------------------------------------------
    # Month logic
    # ---------------------------------------------------------
    def check_month(
        self,
        context: PlanningContext,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        if not work_days:
            return True, []

        label = f"{year}-{month:02d}"

        # Canonical RH input
        rh_days = [rh_day_from_workday(context.agent.id, wd) for wd in work_days]
        rh_days.sort(key=lambda d: d.day_date)

        repos_summary = self.analyzer.summarize_rh_days(rh_days)
        nb_rp_month = repos_summary.total_rest_days

        alerts: List[DomainAlert] = []

        # Partial month: info only (if there is at least one rest day)
        if not is_full:
            if nb_rp_month > 0:
                v = self.info_v(
                    code="B25_MOIS_PARTIEL",
                    msg=(
                        f"[{label}] Régime B25 - Suivi mensuel (mois partiel) : "
                        f"{nb_rp_month} jour(s) de repos."
                    ),
                    start_date=month_start,
                    end_date=month_end,
                    meta={
                        "year": year,
                        "month": month,
                        "label": label,
                        "is_full": is_full,
                        "total_rest_days": nb_rp_month,
                    },
                )
                alerts.append(to_domain_alert(v))
            return True, alerts

        # Full month strict check:
        # - rpsd >= 1
        # - number of rest periods with >=2 days >= 2 (including >=1 rpsd)
        rpsd_count = 0
        rp_2plus_count = 0

        for pr in repos_summary.periods:
            # keep only periods starting in this month window
            if not (month_start <= pr.start <= month_end):
                continue

            if pr.nb_jours >= 2:
                rp_2plus_count += 1
            if pr.is_rpsd():
                rpsd_count += 1

        # Synthesis line (always)
        v = self.info_v(
            code="B25_MOIS_SYNTHESIS",
            msg=(
                f"[{label}] Régime B25 - Repos mensuels : "
                f"RPSD={rpsd_count}, périodes de 2+ jours={rp_2plus_count}."
            ),
            start_date=month_start,
            end_date=month_end,
            meta={
                "year": year,
                "month": month,
                "label": label,
                "is_full": is_full,
                "rpsd": rpsd_count,
                "rp_2plus": rp_2plus_count,
                "min_rpsd": self.MIN_RPSD,
                "min_rp_2plus": self.MIN_RP_2PLUS,
                "total_rest_days": nb_rp_month,
            },
        )
        alerts.append(to_domain_alert(v))

        # Thresholds
        if rpsd_count < self.MIN_RPSD or rp_2plus_count < self.MIN_RP_2PLUS:
            v = self.error_v(
                code="B25_MOIS_NON_CONFORME",
                msg=(
                    f"[{label}] Régime B25 - Repos mensuels insuffisants : "
                    f"RPSD={rpsd_count} (min {self.MIN_RPSD}), "
                    f"RP doubles/2+={rp_2plus_count} (min {self.MIN_RP_2PLUS})."
                ),
                start_date=month_start,
                end_date=month_end,
                meta={
                    "year": year,
                    "month": month,
                    "label": label,
                    "rpsd": rpsd_count,
                    "rp_2plus": rp_2plus_count,
                    "min_rpsd": self.MIN_RPSD,
                    "min_rp_2plus": self.MIN_RP_2PLUS,
                },
            )
            alerts.append(to_domain_alert(v))

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
