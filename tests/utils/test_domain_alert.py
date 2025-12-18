import pytest
from datetime import date

from core.utils.domain_alert import DomainAlert, Severity
from tests.utils.text import strip_ansi


def test_domain_alert_str_includes_all_fields():
    alert = DomainAlert(
        message="Erreur critique",
        severity=Severity.ERROR,
        jour=date(2025, 1, 1),
        source="TestService",
        code="E001",
    )

    raw = str(alert)
    text = strip_ansi(raw)

    lines = text.splitlines()
    assert len(lines) >= 2

    header, body = lines[0], "\n".join(lines[1:])

    # Header : [SEVERITY] 2025-01-01 · TestService · E001
    assert "[ERROR]" in header
    assert "2025-01-01" in header
    assert "TestService" in header
    assert "E001" in header

    # Corps du message
    assert "Erreur critique" in body

    # Après strip_ansi, plus de séquences ANSI
    assert "\033[" not in text


@pytest.mark.parametrize(
    "severity,color_code",
    [
        (Severity.INFO, "\033[94m"),
        (Severity.WARNING, "\033[93m"),
        (Severity.ERROR, "\033[91m"),
        (Severity.SUCCESS, "\033[92m"),
    ],
)
def test_str_color_mapping(severity, color_code):
    """Vérifie que chaque niveau de sévérité utilise bien le bon code couleur."""
    alert = DomainAlert("test", severity=severity)
    raw = str(alert)

    # On vérifie la présence du code couleur brut dans la version non nettoyée
    assert color_code in raw


def test_str_without_colors_when_disabled():
    """Si USE_COLORS=False, aucune séquence ANSI ne doit apparaître."""
    alert = DomainAlert(
        "Message sans couleur",
        severity=Severity.INFO,
        USE_COLORS=False,
    )

    raw = str(alert)
    assert "\033[" not in raw  # aucune séquence ANSI


@pytest.mark.parametrize(
    "severity,expected_error,expected_warning,expected_info",
    [
        (Severity.INFO, False, False, True),
        (Severity.WARNING, False, True, False),
        (Severity.ERROR, True, False, False),
        (Severity.SUCCESS, False, False, False),
    ],
)
def test_is_error_warning_info(severity, expected_error, expected_warning, expected_info):
    alert = DomainAlert("test", severity=severity)
    assert alert.is_error() == expected_error
    assert alert.is_warning() == expected_warning
    assert alert.is_info() == expected_info


def test_domain_alert_without_optional_fields():
    """Alerte sans jour / source / code : format texte simple mais cohérent."""
    alert = DomainAlert("Simple message")
    text = strip_ansi(str(alert))

    lines = text.splitlines()
    assert len(lines) >= 2

    header, body = lines[0], "\n".join(lines[1:])

    # Header minimal : [WARNING]
    assert "[WARNING]" in header
    # Pas de date ni source ni code
    assert "2025-" not in header
    assert "TestService" not in header

    # Le message est présent dans le corps
    assert "Simple message" in body


def test_default_severity_is_warning():
    """Par défaut, la sévérité doit être WARNING."""
    alert = DomainAlert("Test défaut")
    assert alert.severity == Severity.WARNING
    assert alert.is_warning() is True
    assert alert.is_error() is False
    assert alert.is_info() is False


def test_str_includes_severity_header_and_code():
    """La ligne de 'header' doit contenir la sévérité et le code si présent."""
    alert = DomainAlert("Message", severity=Severity.ERROR, code="X42")
    text = strip_ansi(str(alert))

    header = text.splitlines()[0]

    assert "[ERROR]" in header
    assert "X42" in header


def test_str_with_jour_but_no_source_or_code():
    """Jour présent, mais pas de source ni code : la date doit apparaître dans le header."""
    alert = DomainAlert(
        message="Avec date uniquement",
        severity=Severity.INFO,
        jour=date(2025, 2, 3),
    )
    text = strip_ansi(str(alert))

    lines = text.splitlines()
    assert len(lines) >= 2

    header, body = lines[0], "\n".join(lines[1:])

    # Date dans le header (format ISO)
    assert "2025-02-03" in header
    # Message dans le corps
    assert "Avec date uniquement" in body
    # Pas de source ni code
    assert "TestService" not in header
    assert "TestService" not in body


def test_body_is_indented():
    """Le corps du message doit être indenté avec INDENT_MESSAGE."""
    alert = DomainAlert(
        message="Un message de test multilignes potentiellement long.",
        severity=Severity.WARNING,
    )
    text = strip_ansi(str(alert))

    lines = text.splitlines()
    assert len(lines) >= 2

    body_line = lines[1]
    # Au moins la première ligne du corps doit commencer par l'indentation
    assert body_line.startswith(alert.INDENT_MESSAGE)
