# core/rh_rules/rule_amplitude_max.py
from datetime import datetime, timedelta

from core.domain.contexts.planning_context import PlanningContext

from .base_rule import BaseRule
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.tranche_repo import TrancheRepository

class AmplitudeMaxRule(BaseRule):
    name = "amplitude_max"
    description = "Amplitude de travail maximale de 11h"

    def __init__(self, tranche_repo: TrancheRepository, affectation_repo: AffectationRepository):
        self.tranche_repo = tranche_repo
        self.affectation_repo = affectation_repo

    def check(self, context: PlanningContext):
        alerts = []
        affectations = context.get_all_affectations()
        by_day = {}

        for a in affectations:
            by_day.setdefault(a.jour, []).append(a)

        for jour, affs in by_day.items():
            tranches = [a.get_tranche(self.tranche_repo) for a in affs]
            tranches = [t for t in tranches if t is not None]
            if not tranches:
                continue

            debut = min(t.debut for t in tranches)
            fin = max(t.fin for t in tranches)
            amplitude = self._compute_amplitude(debut, fin)

            if amplitude > 11:
                alerts.append(f"⚠️ {jour} : amplitude trop élevée ({amplitude:.1f}h)")

        return alerts

    # ------------------------------------------------------------
    def _compute_amplitude(self, debut, fin) -> float:
        start = datetime.combine(datetime.today(), debut)
        end = datetime.combine(datetime.today(), fin)
        if end < start:
            end += timedelta(days=1)
        return round((end - start).total_seconds() / 3600, 2)
