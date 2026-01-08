# core/rh_rules/rule_grande_periode_travail.py
from __future__ import annotations

from typing import List, Tuple

from core.application.services.planning.grande_periode_travail_analyzer import (
    GrandePeriodeTravailAnalyzer,
)
from core.domain.contexts.planning_context import PlanningContext
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity
from core.utils.time_helpers import minutes_to_duree_str


class GrandePeriodeTravailRule(BaseRule):
    """
    AE Article 34 — Grande Période de Travail (GPT)

    - Durée min : 3 jours (warning uniquement si GPT complète dans la fenêtre)
    - Durée max : 6 jours (error)
    - Charge max : 48 h (error)
    - Si GPT = 6 jours → RP double obligatoire (info)
    """

    name = "GrandePeriodeTravailRule"
    description = "Durée et charge maximale d'une Grande Période de Travail (GPT)."
    scope = RuleScope.PERIOD

    GPT_MIN_JOURS = 3
    GPT_MAX_JOURS = 6
    GPT_MAX_MINUTES = 48 * 60

    def __init__(self, analyzer: GrandePeriodeTravailAnalyzer | None = None):
        self.gpt_service = analyzer or GrandePeriodeTravailAnalyzer()

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        start, end = context.start_date, context.end_date

        if not start or not end:
            v = self.error_v(
                code="GPT_DATES_MISSING",
                msg="Impossible de récupérer la date de début ou de fin.",
                start_date=start,
                end_date=end,
            )
            return False, [to_domain_alert(v)]

        if not context.work_days:
            v = self.info_v(
                code="GPT_NO_WORKDAYS",
                msg="Aucun jour planifié dans le contexte, aucune GPT à analyser.",
                start_date=start,
                end_date=end,
            )
            return True, [to_domain_alert(v)]

        # Canonical RH input (no WorkDay-based RH logic)
        rh_days = [rh_day_from_workday(context.agent.id, wd) for wd in context.work_days]

        # RH-first GPT detection (returns GptBlock)
        gpts = self.gpt_service.detect_from_rh_days(
            rh_days,
            window_start=start,
            window_end=end,
        )

        if not gpts:
            v = self.info_v(
                code="GPT_NONE",
                msg="Aucune Grande Période de Travail détectée.",
                start_date=start,
                end_date=end,
            )
            return True, [to_domain_alert(v)]

        alerts: List[DomainAlert] = []

        count_total = len(gpts)
        count_valid = 0
        count_too_short = 0
        count_too_long = 0
        count_too_loaded = 0
        count_requires_rp_double = 0

        for gpt in gpts:
            nb_jours = gpt.nb_jours
            total_minutes = gpt.total_minutes
            truncated = gpt.is_truncated  # computed by analyzer

            # Too short (< 3 days) -> warning only if fully contained in window
            if nb_jours < self.GPT_MIN_JOURS and not truncated:
                count_too_short += 1
                alerts.append(
                    to_domain_alert(
                        self.warn_v(
                            code="GPT_TROP_COURTE",
                            msg=f"GPT trop courte : {nb_jours} jours (< {self.GPT_MIN_JOURS}).",
                            start_date=gpt.start,
                            end_date=gpt.end,
                            meta={
                                "nb_days": nb_jours,
                                "min_days": self.GPT_MIN_JOURS,
                                "truncated": truncated,
                            },
                        )
                    )
                )
                continue

            # Too long (> 6 days) -> blocking always
            if nb_jours > self.GPT_MAX_JOURS:
                count_too_long += 1
                alerts.append(
                    to_domain_alert(
                        self.error_v(
                            code="GPT_TROP_LONGUE",
                            msg=f"GPT trop longue : {nb_jours} jours (> {self.GPT_MAX_JOURS}).",
                            start_date=gpt.start,
                            end_date=gpt.end,
                            meta={
                                "nb_days": nb_jours,
                                "max_days": self.GPT_MAX_JOURS,
                            },
                        )
                    )
                )
                continue

            # Workload > 48h -> blocking
            if total_minutes > self.GPT_MAX_MINUTES:
                count_too_loaded += 1
                alerts.append(
                    to_domain_alert(
                        self.error_v(
                            code="GPT_CHARGE_TROP_ELEVEE",
                            msg=(
                                "Charge horaire excessive : "
                                f"{minutes_to_duree_str(total_minutes)} "
                                f"(> {minutes_to_duree_str(self.GPT_MAX_MINUTES)})."
                            ),
                            start_date=gpt.start,
                            end_date=gpt.end,
                            meta={
                                "total_minutes": total_minutes,
                                "max_minutes": self.GPT_MAX_MINUTES,
                            },
                        )
                    )
                )

            # GPT = 6 days -> RP double expected
            if nb_jours == self.GPT_MAX_JOURS:
                count_requires_rp_double += 1
                alerts.append(
                    to_domain_alert(
                        self.info_v(
                            code="GPT_RP_DOUBLE_ATTENDU",
                            msg="GPT de 6 jours → repos double obligatoire.",
                            start_date=gpt.start,
                            end_date=gpt.end,
                            meta={"nb_days": nb_jours},
                        )
                    )
                )

            count_valid += 1

        summary = (
            f"{count_total} GPT détectées : "
            f"{count_valid} valides, "
            f"{count_too_short} trop courtes, "
            f"{count_too_long} trop longues, "
            f"{count_too_loaded} > 48h, "
            f"{count_requires_rp_double} nécessitent un RP double."
        )

        alerts.insert(
            0,
            to_domain_alert(
                self.info_v(
                    code="GPT_SYNTHESE",
                    msg=summary,
                    start_date=start,
                    end_date=end,
                    meta={
                        "total": count_total,
                        "valid": count_valid,
                        "too_short": count_too_short,
                        "too_long": count_too_long,
                        "too_loaded": count_too_loaded,
                        "rp_double": count_requires_rp_double,
                    },
                )
            )
        )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
