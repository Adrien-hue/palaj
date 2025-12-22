from core.utils.domain_alert import DomainAlert
from backend.app.dto.common.alerts import DomainAlertDTO

def to_domain_alert_dto(alert: DomainAlert) -> DomainAlertDTO:
    return DomainAlertDTO(
        message=alert.message,
        severity=alert.severity.value,
        jour=alert.jour,
        source=alert.source,
        code=alert.code,
    )
