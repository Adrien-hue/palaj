# core/rh_rules/base_rule.py
from abc import ABC, abstractmethod
from typing import List

from core.domain.contexts.planning_context import PlanningContext


class BaseRule(ABC):
    """Classe de base pour toutes les règles RH."""

    name: str = "BaseRule"
    description: str = ""

    @abstractmethod
    def check(self, context: PlanningContext) -> List[str]:
        """Vérifie la règle et retourne la liste des alertes éventuelles."""
        raise NotImplementedError
