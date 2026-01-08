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


class ReposAnnuelRule(YearRule):
    """
    Annual rest rule:
    - Count rest periods (1/2/3/4+ days)
    - Count RPSD (Sat->Sun) and WERP (Sat->Sun or Sun->Mon)

    Full year: enforce minima (ERROR)
    Partial year: INFO only
    """

    name = "ReposAnnuelRule"
    description = "Analyse annuelle des repos (RP, RP double, RPSD, WERP)."

    MIN_RP_DOUBLE = 52
    MIN_WERP = 14
    MIN_RPSD = 12

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

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
                code="REPOS_ANNUEL_EMPTY_YEAR",
                msg=f"[{year}] Aucun jour planifié sur cette année dans le contexte.",
                start_date=year_start,
                end_date=year_end,
                meta={"year": year, "is_full": is_full},
            )
            return True, [to_domain_alert(v)]

        # Canonical RH input
        rh_days = [rh_day_from_workday(context.agent.id, wd) for wd in work_days]
        rh_days.sort(key=lambda d: d.day_date)

        repos_summary = self.analyzer.summarize_rh_days(rh_days)

        if not repos_summary.periods:
            v = self.info_v(
                code="REPOS_ANNUEL_AUCUN_REPOS",
                msg=f"[{year}] Aucune période de repos détectée.",
                start_date=year_start,
                end_date=year_end,
                meta={"year": year, "is_full": is_full},
            )
            return True, [to_domain_alert(v)]

        rp_simple = repos_summary.rp_simple
        rp_double = repos_summary.rp_double
        rp_triple = repos_summary.rp_triple
        rp_4plus = repos_summary.rp_4plus
        rpsd = repos_summary.rpsd
        werp = repos_summary.werp

        resume_info = (
            f"[{year}] Repos consécutifs détectés : "
            f"{rp_simple} simple(s), {rp_double} double(s), "
            f"{rp_triple} triple(s), {rp_4plus} de 4+ jours. "
            f"RPSD={rpsd}, WERP={werp}."
        )
        alerts.append(
            to_domain_alert(
                self.info_v(
                    code="REPOS_ANNUEL_INFO",
                    msg=resume_info,
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "is_full": is_full,
                        "rp_simple": rp_simple,
                        "rp_double": rp_double,
                        "rp_triple": rp_triple,
                        "rp_4plus": rp_4plus,
                        "rpsd": rpsd,
                        "werp": werp,
                    },
                )
            )
        )

        # Partial year: INFO only
        if not is_full:
            is_valid_partial = all(a.severity != Severity.ERROR for a in alerts)
            return is_valid_partial, alerts

        # Full year: enforce minima
        total_double_equiv = rp_double + rp_triple + rp_4plus

        if total_double_equiv < self.MIN_RP_DOUBLE:
            msg = (
                f"[{year}] Repos doubles insuffisants : "
                f"{total_double_equiv}/{self.MIN_RP_DOUBLE} "
                f"(dont {rp_triple} triples, {rp_4plus} de 4+ jours)."
            )
            alerts.append(
                to_domain_alert(
                    self.error_v(
                        code="REPOS_ANNUEL_RP_DOUBLE_INSUFFISANT",
                        msg=msg,
                        start_date=year_start,
                        end_date=year_end,
                        meta={
                            "year": year,
                            "double_equiv": total_double_equiv,
                            "min_required": self.MIN_RP_DOUBLE,
                            "rp_double": rp_double,
                            "rp_triple": rp_triple,
                            "rp_4plus": rp_4plus,
                        },
                    )
                )
            )

        if werp < self.MIN_WERP:
            alerts.append(
                to_domain_alert(
                    self.error_v(
                        code="REPOS_ANNUEL_WERP_INSUFFISANT",
                        msg=f"[{year}] WERP insuffisants : {werp}/{self.MIN_WERP}.",
                        start_date=year_start,
                        end_date=year_end,
                        meta={"year": year, "werp": werp, "min_required": self.MIN_WERP},
                    )
                )
            )

        if rpsd < self.MIN_RPSD:
            alerts.append(
                to_domain_alert(
                    self.error_v(
                        code="REPOS_ANNUEL_RPSD_INSUFFISANT",
                        msg=f"[{year}] RPSD insuffisants : {rpsd}/{self.MIN_RPSD}.",
                        start_date=year_start,
                        end_date=year_end,
                        meta={"year": year, "rpsd": rpsd, "min_required": self.MIN_RPSD},
                    )
                )
            )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
