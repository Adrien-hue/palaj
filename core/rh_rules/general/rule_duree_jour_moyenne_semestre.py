# core/rh_rules/general/rule_duree_moyenne_regime_semestre.py
from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.semester_rule import SemesterRule
from core.rh_rules.utils.time_calculations import worked_minutes

from core.rh_rules.constants.regime_rules import (
    REGIME_AVG_SERVICE_MINUTES,
    REGIME_AVG_TOLERANCE_MINUTES,
)


class DureeJourMoyenneSemestreRule(SemesterRule):
    """
    Semester average working-day duration by regime.

    - Full semester: ERROR if average not within [target ± tolerance]
    - Partial semester: no violation (engine is "errors only")
    - Not applicable if regime missing/unconfigured: no violation
    """

    name = "DureeMoyenneJourneeRegimeRule"
    description = "Durée moyenne des journées de service par régime, calculée par semestre."

    def check(self, context: RhContext) -> RuleResult:
        # Nothing to do
        if not context.days:
            return RuleResult.ok()

        regime_id = getattr(context.agent, "regime_id", None)

        # Not applicable -> silent OK (engine = errors only)
        if regime_id is None or regime_id not in REGIME_AVG_SERVICE_MINUTES:
            return RuleResult.ok()

        return super().check(context)

    def check_semester(
        self,
        context: RhContext,
        year: int,
        label: str,          # "S1" or "S2"
        sem_start: date,
        sem_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        # Partial semesters: no noise
        if not is_full:
            return RuleResult.ok()

        regime_id = getattr(context.agent, "regime_id", None)
        if regime_id is None or regime_id not in REGIME_AVG_SERVICE_MINUTES:
            return RuleResult.ok()

        target = int(REGIME_AVG_SERVICE_MINUTES[regime_id])
        tol = int(REGIME_AVG_TOLERANCE_MINUTES)

        # Keep only working days (WORKING + ZCOT)
        working_days = [d for d in days if d.is_working()]
        if not working_days:
            return RuleResult.ok()

        # Compute average worked minutes
        total = 0
        for d in working_days:
            total += int(worked_minutes(d))

        nb_days = len(working_days)
        avg = total / nb_days
        delta = float(avg - target)

        if abs(delta) <= tol:
            return RuleResult.ok()

        h_avg = int(avg // 60)
        m_avg = int(avg % 60)
        h_target = int(target // 60)
        m_target = int(target % 60)

        msg = (
            f"[{year} {label}] Durée moyenne de journée non conforme : "
            f"{h_avg}h{m_avg:02d} (objectif {h_target}h{m_target:02d} ± {tol} min) "
            f"sur {nb_days} jour(s) travaillé(s)."
        )

        v = self.error_v(
            code="SEM_DUREE_MOYENNE_NON_CONFORME",
            msg=msg,
            start_date=sem_start,
            end_date=sem_end,
            meta={
                "year": year,
                "label": label,
                "regime_id": regime_id,
                "is_full": is_full,
                "working_days": nb_days,
                "total_minutes": int(total),
                "avg_minutes": float(avg),
                "target_minutes": int(target),
                "tolerance_minutes": int(tol),
                "delta_minutes": float(delta),
            },
        )
        return RuleResult(violations=[v])
