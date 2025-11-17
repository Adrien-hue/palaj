import pytest

from core.data_integrity_checker import DataIntegrityChecker
from core.utils.domain_alert import DomainAlert, Severity


class DummyService:
    def __init__(self, alerts=None):
        self.alerts = list(alerts or [])
        self.calls = 0

    def validate_all(self):
        self.calls += 1
        return [], list(self.alerts)


@pytest.fixture
def checker_services():
    error_alert = DomainAlert("Blocage critique", Severity.ERROR, source="AffectationService")
    warning_alert = DomainAlert("Donnée suspecte", Severity.WARNING, source="AgentService")
    info_alert = DomainAlert("Simple information", Severity.INFO, source="EtatJourAgentService")

    services = [
        DummyService([error_alert]),  # affectation_service
        DummyService([warning_alert]),  # agent_service
        DummyService([info_alert]),  # etat_jour_agent_service
        DummyService([]),  # poste_service
        DummyService([]),  # qualification_service
        DummyService([]),  # regime_service
        DummyService([]),  # tranche_service
    ]

    checker = DataIntegrityChecker(*services)
    return checker, services, (error_alert, warning_alert, info_alert)


def test_run_all_checks_classifies_alerts_and_resets_state(checker_services):
    checker, services, alerts = checker_services
    error_alert, warning_alert, info_alert = alerts

    # Inject stale alerts to ensure run_all_checks clears them before use
    checker.errors.append(DomainAlert("Ancienne erreur", Severity.ERROR))
    checker.warnings.append(DomainAlert("Ancien avertissement"))
    checker.infos.append(DomainAlert("Ancienne info", Severity.INFO))

    result = checker.run_all_checks()

    assert result is False  # at least one blocking error should keep integrity as failing
    assert checker.errors == [error_alert]
    assert checker.warnings == [warning_alert]
    assert checker.infos == [info_alert]

    for service in services:
        assert service.calls == 1


def test_print_report_success_message(capsys):
    services = [DummyService([]) for _ in range(7)]
    checker = DataIntegrityChecker(*services)

    assert checker.run_all_checks() is True
    checker.print_report()

    captured = capsys.readouterr().out
    assert "Aucune anomalie détectée" in captured


def test_print_report_displays_all_alert_levels(checker_services, capsys):
    checker, _, alerts = checker_services
    checker.run_all_checks()
    checker.print_report()

    output = capsys.readouterr().out
    error_alert, warning_alert, info_alert = alerts

    assert "Erreurs critiques" in output
    assert error_alert.message in output
    assert "Avertissements" in output
    assert warning_alert.message in output
    assert "Informations" in output
    assert info_alert.message in output