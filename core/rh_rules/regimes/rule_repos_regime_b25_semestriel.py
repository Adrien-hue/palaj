from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.semester_rule import SemesterRule
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity


class RegimeB25ReposSemestrielRule(SemesterRule):
    """
    Regime B25 (regime_id = 1)

    For each FULL civil semester:
    - At least 56 periodic rest days (RP) per semester:
      - S1: 01/01 -> 30/06
      - S2: 01/07 -> 31/12

    Partial semester:
    - INFO only (no blocking controls)
    """

    name = "RegimeB25ReposSemestrielRule"
    description = "Repos semestriels spécifiques au régime B25 (≥ 56 RP par semestre)."

    MIN_RP_SEMESTRE = 56

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
        return super().check(context)

    # ---------------------------------------------------------
    # Semester logic
    # ---------------------------------------------------------
    def check_semester(
        self,
        context: PlanningContext,
        year: int,
        label: str,  # "S1" or "S2"
        sem_start: date,
        sem_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        # No data for this semester
        if not work_days:
            v = self.info_v(
                code="B25_SEMESTRE_VIDE",
                msg=f"[{year} {label}] Aucun jour planifié sur ce semestre pour l'agent B25.",
                start_date=sem_start,
                end_date=sem_end,
                meta={
                    "year": year,
                    "label": label,
                    "is_full": is_full,
                    "regime_id": 1,
                },
            )
            return True, [to_domain_alert(v)]

        # Canonical RH input
        rh_days = [rh_day_from_workday(context.agent.id, wd) for wd in work_days]
        rh_days.sort(key=lambda d: d.day_date)

        repos_summary = self.analyzer.summarize_rh_days(rh_days)
        nb_rp_sem = repos_summary.total_rest_days

        # Synthesis line (always)
        v = self.info_v(
            code="B25_SEMESTRE_SYNTHESIS",
            msg=(
                f"[{year} {label}] Régime B25 - Repos périodiques sur le semestre "
                f"{sem_start} → {sem_end} : {nb_rp_sem} RP "
                f"(minimum attendu : {self.MIN_RP_SEMESTRE})."
            ),
            start_date=sem_start,
            end_date=sem_end,
            meta={
                "year": year,
                "label": label,
                "is_full": is_full,
                "regime_id": 1,
                "total_rest_days": nb_rp_sem,
                "min_rest_days": self.MIN_RP_SEMESTRE,
                "total_rest_sundays": repos_summary.total_rest_sundays,
            },
        )
        alerts.append(to_domain_alert(v))

        # Partial semester: info only
        if not is_full:
            v = self.info_v(
                code="B25_SEMESTRE_PARTIEL",
                msg=(
                    f"[{year} {label}] Semestre partiellement couvert : "
                    "les minima semestriels B25 ne sont pas contrôlés strictement."
                ),
                start_date=sem_start,
                end_date=sem_end,
                meta={
                    "year": year,
                    "label": label,
                    "regime_id": 1,
                    "min_rest_days": self.MIN_RP_SEMESTRE,
                },
            )
            alerts.append(to_domain_alert(v))
            return True, alerts

        # Full semester: strict check
        if nb_rp_sem < self.MIN_RP_SEMESTRE:
            v = self.error_v(
                code="B25_SEMESTRE_RP_INSUFFISANTS",
                msg=(
                    f"[{year} {label}] Repos périodiques insuffisants pour le régime B25 "
                    f"sur le semestre {sem_start} → {sem_end} : "
                    f"{nb_rp_sem}/{self.MIN_RP_SEMESTRE} jours."
                ),
                start_date=sem_start,
                end_date=sem_end,
                meta={
                    "year": year,
                    "label": label,
                    "regime_id": 1,
                    "total_rest_days": nb_rp_sem,
                    "min_required": self.MIN_RP_SEMESTRE,
                },
            )
            alerts.append(to_domain_alert(v))

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
