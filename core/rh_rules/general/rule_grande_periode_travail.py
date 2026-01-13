# core/rh_rules/rule_grande_periode_travail.py
from __future__ import annotations

from typing import List

from core.rh_rules.base_rule import BaseRule, RuleScope
from core.rh_rules.analyzers.gpt_analyzer import GptAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
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

    def __init__(self, analyzer: GptAnalyzer | None = None):
        self.gpt_service = analyzer or GptAnalyzer()

    def check(self, context: RhContext) -> RuleResult:
        start, end = context.start_date, context.end_date

        if not start or not end:
            v = self.error_v(
                code="GPT_DATES_MISSING",
                msg="Impossible de récupérer la date de début ou de fin.",
                start_date=start,
                end_date=end,
            )
            return RuleResult(violations=[v])

        if not context.days:
            return RuleResult.ok()

        # RH-first GPT detection (returns GptBlock)
        gpts = self.gpt_service.detect_from_rh_days(
            context.days,
            window_start=start,
            window_end=end,
        )

        if not gpts:
            return RuleResult.ok()

        violations: List[RhViolation] = []

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
                violations.append(
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
                continue

            # Too long (> 6 days) -> blocking always
            if nb_jours > self.GPT_MAX_JOURS:
                count_too_long += 1
                violations.append(
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
                continue

            # Workload > 48h -> blocking
            if total_minutes > self.GPT_MAX_MINUTES:
                count_too_loaded += 1
                violations.append(
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

            # GPT = 6 days -> RP double expected
            if nb_jours == self.GPT_MAX_JOURS:
                count_requires_rp_double += 1

            count_valid += 1

        summary = (
            f"{count_total} GPT détectées : "
            f"{count_valid} valides, "
            f"{count_too_short} trop courtes, "
            f"{count_too_long} trop longues, "
            f"{count_too_loaded} > 48h, "
            f"{count_requires_rp_double} nécessitent un RP double."
        )

        violations.insert(
            0,
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

        return RuleResult(violations=violations)
