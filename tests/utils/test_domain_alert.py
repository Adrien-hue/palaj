import pytest
from datetime import date
from core.utils.domain_alert import DomainAlert, Severity
from tests.utils.text import strip_ansi


def test_domain_alert_str_includes_all_fields():
    alert = DomainAlert(
        message="Erreur critique",
        severity=Severity.ERROR,
        jour=date(2025, 1, 1),
        source="TestService"
    )

    result = strip_ansi(str(alert))
    assert "Erreur critique" in result
    assert "TestService" in result
    assert "[2025-01-01]" in result
    assert result.endswith("")  # plus de séquence ANSI


@pytest.mark.parametrize(
    "severity,color_code",
    [
        (Severity.INFO, "\033[94m"),
        (Severity.WARNING, "\033[93m"),
        (Severity.ERROR, "\033[91m"),
        (Severity.SUCCESS, ""),  # Pas de couleur définie pour SUCCESS
    ],
)
def test_str_color_mapping(severity, color_code):
    alert = DomainAlert("test", severity=severity)
    result = str(alert)
    assert color_code in result


@pytest.mark.parametrize(
    "severity,expected_error,expected_warning",
    [
        (Severity.INFO, False, False),
        (Severity.WARNING, False, True),
        (Severity.ERROR, True, False),
        (Severity.SUCCESS, False, False),
    ],
)
def test_is_error_and_is_warning(severity, expected_error, expected_warning):
    alert = DomainAlert("test", severity=severity)
    assert alert.is_error() == expected_error
    assert alert.is_warning() == expected_warning


def test_domain_alert_without_optional_fields():
    """Vérifie qu'une alerte sans jour ni source se convertit correctement en texte."""
    alert = DomainAlert("Simple message")
    result = strip_ansi(str(alert))  # 🔥 nettoyage ANSI

    assert "Simple message" in result
    assert "[" not in result  # aucun jour formaté
    assert "(" not in result  # aucune source affichée
