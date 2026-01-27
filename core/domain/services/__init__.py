# core/domain/services/__init__.py
from core.domain.services.agent_validator_service import AgentValidatorService
from core.domain.services.poste_validator_service import PosteValidatorService
from core.domain.services.qualification_validator_service import QualificationValidatorService
from core.domain.services.regime_validator_service import RegimeValidatorService
from core.domain.services.tranche_validator_service import TrancheValidatorService

agent_validator_service = AgentValidatorService()
poste_validator_service = PosteValidatorService()
qualification_validator_service = QualificationValidatorService()
regime_validator_service = RegimeValidatorService()
tranche_validator_service = TrancheValidatorService()

__all__ = [
    "agent_validator_service",
    "poste_validator_service",
    "qualification_validator_service",
    "regime_validator_service",
    "tranche_validator_service",
]