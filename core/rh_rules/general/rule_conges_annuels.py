from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.application.services.planning.periode_conges_analyzer import PeriodeCongesAnalyzer
from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.year_rule import YearRule
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity

from core.domain.enums.day_type import DayType
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.models.rule_scope import RuleScope


class CongesAnnuelRule(YearRule):
    """
    Annual leave rule:
    - 28 annual leave days (DayType.LEAVE)
    - at least one leave block (leave + rest) of 15 consecutive days
    """

    name = "CongesAnnuelRule"
    description = "Contrôle annuel des congés (quotas et périodes longues)."

    MIN_CONGES_ANNUELS = 28
    MIN_CONGE_BLOCK = 15

    def __init__(self, analyzer: PeriodeCongesAnalyzer | None = None) -> None:
        self.analyzer = analyzer or PeriodeCongesAnalyzer()

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

        if not work_days:
            v = self.info_v(
                code="CONGES_ANNUELS_EMPTY_YEAR",
                msg=f"[{year}] Aucun jour planifié sur cette année dans le contexte.",
                start_date=year_start,
                end_date=year_end,
                meta={"year": year, "is_full": is_full},
            )
            return True, [to_domain_alert(v)]

        # Canonical RH input
        rh_days = [rh_day_from_workday(context.agent.id, wd) for wd in work_days]
        rh_days.sort(key=lambda d: d.day_date)

        # RH-first analyzer
        periodes = self.analyzer.detect_from_rh_days(rh_days)

        # Count annual leave days from DayType
        total_conges = sum(1 for d in rh_days if d.day_type == DayType.LEAVE)

        longest_block = max((p.nb_jours for p in periodes), default=0)
        nb_blocks_15_plus = sum(1 for p in periodes if p.nb_jours >= self.MIN_CONGE_BLOCK)

        summary = (
            f"[{year}] Congés annuels : {total_conges} jour(s) pris. "
            f"Période de congés (congé+repos) la plus longue : {longest_block} jour(s). "
            f"Périodes de congés ≥ {self.MIN_CONGE_BLOCK} jours : {nb_blocks_15_plus}."
        )

        alerts.append(
            to_domain_alert(
                self.info_v(
                    code="CONGES_ANNUELS_SYNTHESIS",
                    msg=summary,
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "is_full": is_full,
                        "total_leave_days": total_conges,
                        "longest_block_days": longest_block,
                        "blocks_15_plus": nb_blocks_15_plus,
                    },
                )
            )
        )

        if is_full:
            if total_conges < self.MIN_CONGES_ANNUELS:
                alerts.append(
                    to_domain_alert(
                        self.error_v(
                            code="CONGES_ANNUELS_QUOTA_INSUFFISANT",
                            msg=f"[{year}] Nombre de congés annuels insuffisant : {total_conges}/{self.MIN_CONGES_ANNUELS}.",
                            start_date=year_start,
                            end_date=year_end,
                            meta={
                                "year": year,
                                "leave_days": total_conges,
                                "min_required": self.MIN_CONGES_ANNUELS,
                            },
                        )
                    )
                )

            if nb_blocks_15_plus == 0:
                alerts.append(
                    to_domain_alert(
                        self.error_v(
                            code="CONGES_ANNUELS_BLOC_LONG_MANQUANT",
                            msg=(
                                f"[{year}] Aucune période de congés consécutifs "
                                f"(congé + repos) de {self.MIN_CONGE_BLOCK} jours ou plus détectée."
                            ),
                            start_date=year_start,
                            end_date=year_end,
                            meta={"year": year, "min_block_days": self.MIN_CONGE_BLOCK},
                        )
                    )
                )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
