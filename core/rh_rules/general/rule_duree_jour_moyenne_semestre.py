from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.models.rule_scope import RuleScope
from core.rh_rules.semester_rule import SemesterRule
from core.rh_rules.utils.time_calculations import worked_minutes
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity

from core.rh_rules.constants.regime_rules import (
    REGIME_AVG_SERVICE_MINUTES,
    REGIME_AVG_TOLERANCE_MINUTES,
)


class DureeJourMoyenneSemestreRule(SemesterRule):
    """
    Semester average working-day duration by regime.
    Full semester: ERROR if avg not within [target ± tol]
    Partial semester: INFO only
    """

    name = "DureeMoyenneJourneeRegimeRule"
    description = "Durée moyenne des journées de service par régime, calculée par semestre."

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        # 1) No days -> nothing to analyze
        if not context.work_days:
            return True, []

        agent = context.agent
        regime_id = getattr(agent, "regime_id", None)

        # 2) Not applicable if no configured regime
        if regime_id is None or regime_id not in REGIME_AVG_SERVICE_MINUTES:
            v = self.info_v(
                code="SEM_DUREE_MOYENNE_REGIME_INCONNU",
                msg=(
                    "Règle de durée moyenne non applicable : "
                    "régime inconnu ou non configuré."
                ),
                start_date=context.start_date,
                end_date=context.end_date,
                meta={"regime_id": regime_id},
            )
            return True, [to_domain_alert(v)]

        return super().check(context)

    def check_semester(
        self,
        context: PlanningContext,
        year: int,
        label: str,          # "S1" or "S2"
        sem_start: date,
        sem_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        agent = context.agent
        regime_id = getattr(agent, "regime_id", None)
        if regime_id is None or regime_id not in REGIME_AVG_SERVICE_MINUTES:
            return True, []

        target = int(REGIME_AVG_SERVICE_MINUTES[regime_id])
        tol = int(REGIME_AVG_TOLERANCE_MINUTES)

        # Build canonical RH days for this semester slice
        rh_days = [rh_day_from_workday(context.agent.id, wd) for wd in work_days]

        # Keep only working days
        rh_working = [d for d in rh_days if d.is_working()]
        if not rh_working:
            v = self.info_v(
                code="SEM_DUREE_MOYENNE_AUCUN_JOUR",
                msg=f"{label} : aucun jour travaillé sur la période analysée.",
                start_date=sem_start,
                end_date=sem_end,
                meta={"year": year, "label": label, "regime_id": regime_id, "is_full": is_full},
            )
            return True, [to_domain_alert(v)]

        # Average worked minutes
        minutes_list = [int(worked_minutes(d)) for d in rh_working]
        total_minutes = sum(minutes_list)
        nb_days = len(minutes_list)
        avg_minutes = total_minutes / nb_days

        h = int(avg_minutes // 60)
        m = int(avg_minutes % 60)
        h_target = target // 60
        m_target = target % 60

        base_msg = (
            f"{label} – durée moyenne de journée : "
            f"{h}h{m:02d} (objectif : {h_target}h{m_target:02d} ± {tol} min) "
            f"sur {nb_days} jour(s) travaillé(s)."
        )

        meta = {
            "year": year,
            "label": label,
            "regime_id": regime_id,
            "is_full": is_full,
            "avg_minutes": float(avg_minutes),
            "target_minutes": target,
            "tolerance_minutes": tol,
            "working_days": nb_days,
        }

        if is_full:
            if abs(avg_minutes - target) > tol:
                v = self.error_v(
                    code="SEM_DUREE_MOYENNE_NON_CONFORME",
                    msg=base_msg + " Non conforme pour le semestre complet.",
                    start_date=sem_start,
                    end_date=sem_end,
                    meta=meta,
                )
                alerts.append(to_domain_alert(v))
            else:
                v = self.info_v(
                    code="SEM_DUREE_MOYENNE_CONFORME",
                    msg=base_msg + " Conforme pour le semestre complet.",
                    start_date=sem_start,
                    end_date=sem_end,
                    meta=meta,
                )
                alerts.append(to_domain_alert(v))
        else:
            v = self.info_v(
                code="SEM_DUREE_MOYENNE_PARTIEL",
                msg=base_msg + " Période incomplète : suivi indicatif uniquement.",
                start_date=sem_start,
                end_date=sem_end,
                meta=meta,
            )
            alerts.append(to_domain_alert(v))

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
