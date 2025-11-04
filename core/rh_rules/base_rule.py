# core/rh_rules/base_rule.py
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple, Optional
from datetime import date

from core.utils.domain_alert import DomainAlert, Severity

class RuleScope(Enum):
    DAY = "day"
    PERIOD = "period"

class BaseRule(ABC):
    """Classe de base pour toutes les règles RH."""

    name: str = "BaseRule"
    description: str = ""
    scope: RuleScope = RuleScope.DAY
    priority: int = 1  # 1 = critique, 2 = moyenne, 3 = info

    def __init__(self):
        pass

    @abstractmethod
    def check(self, context) -> Tuple[bool, List[DomainAlert]]:
        """
        Vérifie la règle et retourne (is_valid, [DomainAlert])
        Le paramètre `context` contient le planning ou agent concerné.
        """
        pass

    # Pour les règles “jour”
    def check_day(self, context, jour) -> Tuple[bool, List[DomainAlert]]:
        raise NotImplementedError(f"{self.name} n'implémente pas check_day")

    # Pour les règles “période” (multi-jours)
    def check_period(self, context) -> Tuple[bool, List[DomainAlert]]:
        raise NotImplementedError(f"{self.name} n'implémente pas check_period")

    # --- Helpers ---
    def _alert(
        self,
        message: str,
        severity: Severity,
        jour: Optional[date] = None
    ) -> DomainAlert:
        """Crée une alerte standardisée pour cette règle."""
        return DomainAlert(
            message=message,
            severity=severity,
            jour=jour,
            source=self.name,
        )
