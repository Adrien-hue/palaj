# domain/services/rh_rules_service.py
from typing import List

from core.rh_rules.rule_repos_quotidien import ReposQuotidienRule
from core.rh_rules.rule_amplitude_max import AmplitudeMaxRule
from core.rh_rules.rule_duree_travail import DureeTravailRule
from core.rh_rules.rule_travail_nuit import TravailNuitRule

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.tranche_repo import TrancheRepository

class RHRulesService:
    """
    Service de haut niveau : orchestre toutes les règles RH pour un agent.
    """

    def __init__(self, tranche_repo: TrancheRepository, affectation_repo: AffectationRepository):
        # On instancie les règles RH de core/
        self.rules = [
            ReposQuotidienRule(tranche_repo, affectation_repo),
            AmplitudeMaxRule(tranche_repo, affectation_repo),
            DureeTravailRule(tranche_repo, affectation_repo),
            TravailNuitRule(tranche_repo, affectation_repo),
        ]

    def check_all(self, agent_id: int) -> List[str]:
        """Applique toutes les règles RH et agrège les alertes."""
        all_alerts = []
        for rule in self.rules:
            results = rule.check(agent_id)
            if results:
                all_alerts.extend(results)
        return all_alerts

    def check_rule(self, rule_name: str, agent_id: int) -> List[str]:
        """Applique une règle RH spécifique."""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule.check(agent_id)
        raise ValueError(f"Règle RH '{rule_name}' introuvable.")
