from __future__ import annotations

from datetime import timedelta
from typing import List

from core.domain.enums.day_type import DayType
from core.rh_rules.analyzers.gpt_analyzer import GptAnalyzer
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult


class ReposDoubleRule(BaseRule):
    """
    After a complete 6-day GPT (fully started inside the window),
    the agent must have at least 2 consecutive REST days immediately after.
    """

    name = "ReposDoubleRule"
    description = "Vérifie la présence d'un repos double après une GPT complète de 6 jours."
    scope = RuleScope.PERIOD

    NB_JOURS_REPOS_MIN = 2
    GPT_TARGET_DAYS = 6

    def __init__(self, analyzer: GptAnalyzer | None = None):
        self.gpt_service = analyzer or GptAnalyzer()

    def check(self, context: RhContext) -> RuleResult:
        if not context.days:
            return RuleResult.ok()

        start = context.effective_start
        end = context.effective_end

        # Uniformize with other PERIOD rules
        if not start or not end:
            v = self.error_v(
                code="REPOS_DOUBLE_DATES_MISSING",
                msg="Impossible de récupérer la date de début ou de fin pour vérifier le repos double.",
                start_date=start,
                end_date=end,
            )
            return RuleResult(violations=[v])

        gpts = self.gpt_service.detect_from_rh_days(
            context.days,
            window_start=start,
            window_end=end,
        )
        if not gpts:
            return RuleResult.ok()

        by_date = context.by_date
        violations: List[RhViolation] = []

        for gpt in gpts:
            # Ignore left-truncated blocks (partial start)
            if gpt.is_left_truncated:
                continue

            # Must be exactly 6 days
            if gpt.nb_jours != self.GPT_TARGET_DAYS:
                continue

            # Context must include at least the needed days after GPT end to judge
            last_needed_day = gpt.end + timedelta(days=self.NB_JOURS_REPOS_MIN)
            if last_needed_day > end:
                continue

            # Count consecutive REST days right after GPT end
            consecutive_rest = 0
            for i in range(1, self.NB_JOURS_REPOS_MIN + 1):
                d = gpt.end + timedelta(days=i)
                rh_day = by_date.get(d)
                if rh_day and rh_day.day_type == DayType.REST:
                    consecutive_rest += 1
                else:
                    break

            if consecutive_rest < self.NB_JOURS_REPOS_MIN:
                violations.append(
                    self.error_v(
                        code="REPOS_DOUBLE_MANQUANT",
                        msg=(
                            "Repos double manquant après GPT de 6 jours : "
                            f"{consecutive_rest} jour(s) détecté(s), "
                            f"attendu ≥ {self.NB_JOURS_REPOS_MIN}."
                        ),
                        start_date=gpt.start,
                        end_date=last_needed_day,
                        meta={
                            "gpt_start": str(gpt.start),
                            "gpt_end": str(gpt.end),
                            "required_rest_days": self.NB_JOURS_REPOS_MIN,
                            "detected_rest_days": consecutive_rest,
                            "is_left_truncated": gpt.is_left_truncated,
                            "is_right_truncated": gpt.is_right_truncated,
                        },
                    )
                )

        return RuleResult(violations=violations)