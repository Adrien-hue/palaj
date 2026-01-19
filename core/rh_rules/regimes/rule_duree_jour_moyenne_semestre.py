from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.semester_rule import SemesterRule
from core.rh_rules.utils.time_calculations import worked_minutes


class DureeJourMoyenneSemestreRule(SemesterRule):
    """
    Semester average working-day duration by regime.

    - Full semester: ERROR if average not within [target ± tolerance]
    - Partial semester: no violation (engine is "errors only")
    - Not applicable if regime missing/unconfigured: no violation
    """

    name = "DureeMoyenneJourneeRegimeRule"
    description = "Durée moyenne des journées de service par régime, calculée par semestre."

    def _get_regime(self, context: RhContext):
        # Prefer full regime object if present (new model)
        regime = getattr(context.agent, "regime", None)
        if regime is not None:
            return regime

        # Backward compatibility: if only regime_id exists, we can't compute targets here
        return None

    def check(self, context: RhContext) -> RuleResult:
        if not context.days:
            return RuleResult.ok()

        regime = self._get_regime(context)

        # Not applicable -> silent OK (engine = errors only)
        if regime is None:
            return RuleResult.ok()

        # If avg is not configured anywhere (even via default), you could decide to skip.
        # Here we assume effective_* always returns a usable value.
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
        if not is_full:
            return RuleResult.ok()

        regime = self._get_regime(context)
        if regime is None:
            return RuleResult.ok()

        target = int(regime.effective_avg_service_minutes)
        tol = int(regime.effective_avg_tolerance_minutes)

        # Keep only working days (WORKING + ZCOT)
        working_days = [d for d in days if d.is_working()]
        if not working_days:
            return RuleResult.ok()

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

        # regime_id still useful for meta/debug (if available)
        regime_id = getattr(context.agent, "regime_id", None)

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
                "regime_name": getattr(regime, "nom", None),
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
