# core/rh_rules/rule_amplitude_max.py
from .base_rule import BaseRule
from datetime import datetime, timedelta

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.tranche_repo import TrancheRepository

class AmplitudeMaxRule(BaseRule):
    name = "amplitude_max"
    description = "Amplitude de travail maximale de 11h"

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
            if len(affs) > 1:
                continue  # un seul créneau par jour, donc amplitude triviale

            tranche = affs[0].get_tranche(self.tranche_repo)
            if not tranche:
                continue

            duree = tranche.duree()
            if duree > 11:
                alerts.append(f"⚠️ {jour} : amplitude trop élevée ({duree:.1f}h)")

        return alerts
