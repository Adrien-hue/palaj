# core/rh_rules/rule_duree_travail.py
from .base_rule import BaseRule
from datetime import time

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.tranche_repo import TrancheRepository

class DureeTravailRule(BaseRule):
    name = "duree_travail"
    description = "Durée totale de travail journalière"

    def __init__(self, tranche_repo: TrancheRepository, affectation_repo: AffectationRepository):
        self.tranche_repo = tranche_repo
        self.affectation_repo = affectation_repo

    def check(self, agent_id: int):
        alerts = []
        affectations = self.affectation_repo.list_for_agent(agent_id)
        by_day = {}

        for a in affectations:
            by_day.setdefault(a.jour, []).append(a)

        for jour, affs in by_day.items():
            tranches = [a.get_tranche(self.tranche_repo) for a in affs if a.get_tranche(self.tranche_repo)]
            total = sum(t.duree() for t in tranches)
            nocturnes = [self._is_nocturne(t) for t in tranches]
            travail_nuit = any(nocturnes)

            max_allowed = 8.5 if travail_nuit else 10.0

            if total < 5.5:
                alerts.append(f"⚠️ {jour} : durée de travail trop courte ({total:.2f}h < 5.5h)")
            elif total > max_allowed:
                alerts.append(f"⚠️ {jour} : durée de travail excessive ({total:.2f}h > {max_allowed}h)")
        return alerts

    def _is_nocturne(self, tranche):
        return tranche.debut >= time(21, 30) or tranche.fin <= time(6, 30)
