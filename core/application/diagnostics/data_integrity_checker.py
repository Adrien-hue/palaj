# core/application/services/data_integrity_checker.py
from typing import List

from core.application.services.container import (
    agent_service,
    poste_service,
    tranche_service,
    qualification_service,
    affectation_service,
    etat_jour_agent_service,
    regime_service,
)

from core.domain.services import (
    agent_validator_service,
    poste_validator_service,
    tranche_validator_service,
    qualification_validator_service,
    affectation_validator_service,
    etat_jour_agent_validator_service,
    regime_validator_service,
)

from core.utils.domain_alert import DomainAlert, Severity



class DataIntegrityChecker:
    """
    🧪 Vérifie la cohérence globale des données de ton domaine.
    Combine :
    - Services applicatifs → chargent les entités depuis la DB
    - Validators métier → appliquent les règles RH
    """

    def __init__(self):
        # Services applicatifs
        self.agent_service = agent_service
        self.poste_service = poste_service
        self.tranche_service = tranche_service
        self.qualification_service = qualification_service
        self.affectation_service = affectation_service
        self.etat_jour_service = etat_jour_agent_service
        self.regime_service = regime_service

        # Validators métier
        self.agent_validator = agent_validator_service
        self.poste_validator = poste_validator_service
        self.tranche_validator = tranche_validator_service
        self.qualification_validator = qualification_validator_service
        self.affectation_validator = affectation_validator_service
        self.etat_jour_validator = etat_jour_agent_validator_service
        self.regime_validator = regime_validator_service

        # Stockage du rapport
        self.errors: List[DomainAlert] = []
        self.warnings: List[DomainAlert] = []
        self.infos: List[DomainAlert] = []

    # ============================================================
    # 🔍 Vérifications
    # ============================================================

    def check_agents(self):
        agents = self.agent_service.list_agents_complets()
        ok, alerts = self.agent_validator.validate_all(agents)
        self._register(alerts)

    def check_regimes(self):
        regimes = self.regime_service.list_regimes_complets()
        ok, alerts = self.regime_validator.validate_all(regimes)
        self._register(alerts)

    def check_tranches(self):
        tranches = self.tranche_service.list_tranches_complets()
        ok, alerts = self.tranche_validator.validate_all(tranches)
        self._register(alerts)

    def check_postes(self):
        postes = self.poste_service.list_postes_complets()
        ok, alerts = self.poste_validator.validate_all(postes)
        self._register(alerts)

    def check_qualifications(self):
        qualifications = self.qualification_service.list_qualifications()
        ok, alerts = self.qualification_validator.validate_all(qualifications)
        self._register(alerts)

    def check_affectations(self):
        affectations = self.affectation_service.list_affectations_completes()
        ok, alerts = self.affectation_validator.validate_all(affectations)
        self._register(alerts)

    def check_etats_jour(self):
        etats = self.etat_jour_service.list_etats_jour_agent_complets()
        ok, alerts = self.etat_jour_validator.validate_all(etats)
        self._register(alerts)

    # ============================================================
    # 🔧 Utils
    # ============================================================

    def _register(self, alerts: List[DomainAlert]):
        """Classe les alertes selon leur type."""
        for a in alerts:
            if a.severity == Severity.ERROR:
                self.errors.append(a)
            elif a.severity == Severity.WARNING:
                self.warnings.append(a)
            else:
                self.infos.append(a)

    def _reset(self):
        """Réinitialise les alertes."""
        self.errors.clear()
        self.warnings.clear()
        self.infos.clear()

    # ============================================================
    # 🚀 Orchestration complète
    # ============================================================

    def run_all_checks(self) -> dict[str, List[DomainAlert]]:
        """Exécute toutes les vérifications globales."""
        self._reset()

        self.check_agents()
        self.check_regimes()
        self.check_tranches()
        self.check_postes()
        self.check_qualifications()
        self.check_affectations()
        self.check_etats_jour()

        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
        }