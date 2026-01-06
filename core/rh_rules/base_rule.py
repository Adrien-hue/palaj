# core/rh_rules/base_rule.py
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from datetime import date

from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_scope import RuleScope
from core.utils.domain_alert import DomainAlert, Severity

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
    
    def _violation(
        self,
        message: str,
        severity: Severity,
        code: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        start_dt=None,
        end_dt=None,
        meta: dict | None = None,
    ) -> RhViolation:
        return RhViolation(
            code=code,
            rule_name=self.name,
            severity=severity,
            message=message,
            scope=self.scope,
            start_date=start_date,
            end_date=end_date,
            start_dt=start_dt,
            end_dt=end_dt,
            meta=meta or {},
        )

    def error_v(self, msg: str, code: str, **kwargs) -> RhViolation:
        return self._violation(msg, Severity.ERROR, code, **kwargs)

    def info_v(self, msg: str, code: str, **kwargs) -> RhViolation:
        return self._violation(msg, Severity.INFO, code, **kwargs)

    def warn_v(self, msg: str, code: str, **kwargs) -> RhViolation:
        return self._violation(msg, Severity.WARNING, code, **kwargs)