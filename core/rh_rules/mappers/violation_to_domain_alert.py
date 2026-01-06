# core/rh_rules/mappers/violation_to_domain_alert.py
from core.utils.domain_alert import DomainAlert
from core.rh_rules.models.rh_violation import RhViolation

def to_domain_alert(v: RhViolation) -> DomainAlert:
    return DomainAlert(
        message=v.message,
        severity=v.severity,
        jour=v.start_date,      # pour garder un minimum d’ancrage date
        source=v.rule_name,     # utile pour debug
        code=v.code,
    )
