from __future__ import annotations

from datetime import timedelta
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.enums.day_type import DayType
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.analyzers.gpt_analyzer import GptAnalyzer
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity


class ReposDoubleRule(BaseRule):
    """
    After a complete 6-day GPT, the agent must have at least 2 consecutive REST days.
    """

    name = "ReposDoubleRule"
    description = "Vérifie la présence d'un repos double après une GPT complète de 6 jours."
    scope = RuleScope.PERIOD

    NB_JOURS_REPOS_MIN = 2

    def __init__(self, analyzer: GptAnalyzer | None = None):
        self.gpt_service = analyzer or GptAnalyzer()

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        if not context.work_days:
            return True, []

        start, end = context.start_date, context.end_date
        if not start or not end:
            # Comportement: l’ancienne règle ne gérait pas ce cas explicitement,
            # mais BaseRule le fait souvent. Ici on reste soft:
            return True, []

        # Canonical RH days
        rh_days = [rh_day_from_workday(context.agent.id, wd) for wd in context.work_days]
        rh_days.sort(key=lambda d: d.day_date)

        # GPT blocks from RH-first analyzer (returns GptBlock)
        gpts = self.gpt_service.detect_from_rh_days(
            rh_days,
            window_start=start,
            window_end=end,
        )
        if not gpts:
            return True, []

        # We need quick access by date for post-GPT checks
        rh_by_date = {d.day_date: d for d in rh_days}
        all_dates = sorted(rh_by_date.keys())

        alerts: List[DomainAlert] = []

        for gpt in gpts:
            if gpt.is_left_truncated:
                continue

            if gpt.nb_jours != 6:
                continue

            # Ensure we have at least NB_JOURS_REPOS_MIN dates after GPT end in the context
            days_after = [d for d in all_dates if d > gpt.end]
            if len(days_after) < self.NB_JOURS_REPOS_MIN:
                continue  # context too short to judge

            # Count consecutive REST days starting the day after GPT end
            consecutive_rest = 0
            for i in range(1, self.NB_JOURS_REPOS_MIN + 1):
                day = gpt.end + timedelta(days=i)
                d = rh_by_date.get(day)
                if d and d.day_type == DayType.REST:
                    consecutive_rest += 1
                else:
                    break

            if consecutive_rest < self.NB_JOURS_REPOS_MIN:
                v = self.error_v(
                    code="REPOS_DOUBLE_MANQUANT",
                    msg=(
                        "Repos double manquant après GPT de 6 jours : "
                        f"{consecutive_rest} jour(s) détecté(s), "
                        f"attendu ≥ {self.NB_JOURS_REPOS_MIN}."
                    ),
                    start_date=gpt.start,
                    end_date=gpt.end + timedelta(days=self.NB_JOURS_REPOS_MIN),
                    start_dt=None,
                    end_dt=None,
                    meta={
                        "gpt_start": str(gpt.start),
                        "gpt_end": str(gpt.end),
                        "required_rest_days": self.NB_JOURS_REPOS_MIN,
                        "detected_rest_days": consecutive_rest,
                        "is_left_truncated": getattr(gpt, "is_left_truncated", False),
                        "is_right_truncated": getattr(gpt, "is_right_truncated", False),
                    },
                )
                alerts.append(to_domain_alert(v))

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
