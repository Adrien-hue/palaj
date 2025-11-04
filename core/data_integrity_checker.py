from typing import List

from core.utils.domain_alert import DomainAlert, Severity

from core.domain.services.affectation_service import AffectationService
from core.domain.services.agent_service import AgentService
from core.domain.services.etat_jour_agent_service import EtatJourAgentService
from core.domain.services.poste_service import PosteService
from core.domain.services.qualification_service import QualificationService
from core.domain.services.tranche_service import TrancheService
from core.domain.services.regime_service import RegimeService

class DataIntegrityChecker:
    """
    Vérifie la cohérence globale du domaine via les services métiers :
    - Affectations
    - Agents
    - États journaliers
    - Postes
    - Qualifications
    - Tranches
    - Régimes
    """

    def __init__(
        self,
        affectation_service: AffectationService,
        agent_service: AgentService,
        etat_jour_agent_service: EtatJourAgentService,
        poste_service: PosteService,
        qualification_service: QualificationService,
        regime_service: RegimeService,
        tranche_service: TrancheService,
    ):
        self.agent_service = agent_service
        self.poste_service = poste_service
        self.tranche_service = tranche_service
        self.qualification_service = qualification_service
        self.affectation_service = affectation_service
        self.etat_jour_agent_service = etat_jour_agent_service
        self.regime_service = regime_service

        self.errors: List[DomainAlert] = []
        self.warnings: List[DomainAlert] = []
        self.infos: List[DomainAlert] = []

    # ----------------------------
    # Vérifications principales
    # ----------------------------

    def check_agents(self):
        _, alerts = self.agent_service.validate_all()
        self._register_alerts(alerts)

    def check_postes(self):
        _, alerts = self.poste_service.validate_all()
        self._register_alerts(alerts)

    def check_tranches(self):
        _, alerts = self.tranche_service.validate_all()
        self._register_alerts(alerts)

    def check_qualifications(self):
        _, alerts = self.qualification_service.validate_all()
        self._register_alerts(alerts)

    def check_affectations(self):
        _, alerts = self.affectation_service.validate_all()
        self._register_alerts(alerts)

    def check_etats_jour(self):
        _, alerts = self.etat_jour_agent_service.validate_all()
        self._register_alerts(alerts)

    def check_regimes(self):
        _, alerts = self.regime_service.validate_all()
        self._register_alerts(alerts)

    # ----------------------------
    # Utilitaires internes
    # ----------------------------

    def _register_alerts(self, alerts: List[DomainAlert]):
        """Classe les alertes selon leur sévérité."""
        for a in alerts:
            if a.severity == Severity.ERROR:
                self.errors.append(a)
            elif a.severity == Severity.WARNING:
                self.warnings.append(a)
            else:
                self.infos.append(a)

    # ----------------------------
    # Orchestration complète
    # ----------------------------

    def run_all_checks(self) -> bool:
        """Exécute toutes les vérifications globales du système."""
        self.errors.clear()
        self.warnings.clear()
        self.infos.clear()

        self.check_agents()
        self.check_postes()
        self.check_tranches()
        self.check_qualifications()
        self.check_affectations()
        self.check_etats_jour()
        self.check_regimes()

        return len(self.errors) == 0

    # ----------------------------
    # Affichage lisible du rapport
    # ----------------------------

    def print_report(self):
        """Affiche un rapport coloré et clair des anomalies détectées."""
        BOLD = "\033[1m"
        RESET = "\033[0m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        GRAY = "\033[90m"
        GREEN = "\033[92m"

        print(f"\n{BOLD}{CYAN}🧪 === Rapport d'intégrité des données ==={RESET}\n")

        if not self.errors and not self.warnings:
            print(f"{GREEN}✅ Aucune anomalie détectée !{RESET}")
            return

        if self.errors:
            print(f"{RED}{BOLD}❌ Erreurs critiques :{RESET}")
            for e in self.errors:
                print(f"  - {e.message} ({e.source})")
            print()

        if self.warnings:
            print(f"{YELLOW}{BOLD}⚠️ Avertissements :{RESET}")
            for w in self.warnings:
                print(f"  - {w.message} ({w.source})")
            print()

        if self.infos:
            print(f"{GRAY}{BOLD}ℹ️ Informations :{RESET}")
            for i in self.infos:
                print(f"  - {i.message} ({i.source})")

        print(f"\n{CYAN}--- Fin du rapport ---{RESET}\n")
