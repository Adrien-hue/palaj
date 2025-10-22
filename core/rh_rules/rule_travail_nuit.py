# core/rh_rules/rule_travail_nuit.py
from .base_rule import BaseRule
from datetime import time

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.tranche_repo import TrancheRepository

class TravailNuitRule(BaseRule):
    name = "travail_nuit"
    description = "Travail effectué pendant la période nocturne (21h30 - 6h30)"

    HEURE_NUIT_DEBUT = time(21, 30)
    HEURE_NUIT_FIN = time(6, 30)

    def __init__(self, tranche_repo: TrancheRepository, affectation_repo: AffectationRepository):
        self.tranche_repo = tranche_repo
        self.affectation_repo = affectation_repo

    def check(self, agent_id: int):
        alerts = []
        affectations = self.affectation_repo.list_for_agent(agent_id)

        for a in affectations:
            tranche = a.get_tranche(self.tranche_repo)
            if not tranche:
                continue

            if tranche.debut >= self.HEURE_NUIT_DEBUT or tranche.fin <= self.HEURE_NUIT_FIN:
                alerts.append(f"🌙 {a.jour} : travail de nuit détecté ({tranche.abbr})")

        return alerts
