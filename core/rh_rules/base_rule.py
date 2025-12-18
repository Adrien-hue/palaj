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

    def __init__(self):
        pass

    def applies_to(self, context) -> bool:
        """
        Par défaut : la règle s'applique à tous les contextes.
        Les règles spécifiques (par régime, par métier, etc.)
        peuvent surcharger cette méthode.
        """
        return True

    @abstractmethod
    def check(self, context) -> Tuple[bool, List[DomainAlert]]:
        """
        Vérifie la règle et retourne (is_valid, [DomainAlert])
        Le paramètre `context` contient le planning ou agent concerné.
        """
        pass

    # --- Helpers ---
    def _alert(
        self,
        message: str,
        severity: Severity,
        jour: Optional[date] = None,
        code: Optional[str] = None,
    ) -> DomainAlert:
        """Crée une alerte standardisée pour cette règle."""
        return DomainAlert(
            message=message,
            severity=severity,
            jour=jour,
            source=self.name,
            code=code,
        )
    
    def info(self, msg: str, jour: Optional[date] = None, code: Optional[str] = None) -> DomainAlert:
        return self._alert(message=msg, severity=Severity.INFO, jour=jour, code=code)
    
    def warn(self, msg: str, jour: Optional[date] = None, code: Optional[str] = None) -> DomainAlert:
        return self._alert(message=msg, severity=Severity.WARNING, jour=jour, code=code)
    
    def error(self, msg: str, jour: Optional[date] = None, code: Optional[str] = None) -> DomainAlert:
        return self._alert(message=msg, severity=Severity.ERROR, jour=jour, code=code)