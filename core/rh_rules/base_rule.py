# core/rh_rules/base_rule.py
from abc import ABC, abstractmethod
from typing import List

class BaseRule(ABC):
    """Classe de base pour toutes les règles RH."""

    name: str = "BaseRule"
    description: str = ""

    @abstractmethod
    def check(self, agent_id: int) -> List[str]:
        """Vérifie la règle et retourne la liste des alertes éventuelles."""
        pass
