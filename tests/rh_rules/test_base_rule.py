import pytest
from datetime import date

from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity


# ---------------------------------------------------------------------
# Règle concrète minimale pour tester BaseRule
# ---------------------------------------------------------------------


class DummyRule(BaseRule):
    name = "DummyRule"
    description = "Règle de test"
    scope = RuleScope.DAY

    def check(self, context):
        # On retourne une alerte info simple pour tester la signature
        alert = self.info("Tout va bien", code="DUMMY_OK")
        return True, [alert]


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_base_rule_is_abstract():
    """BaseRule ne doit pas être instanciable directement (méthode abstraite)."""
    with pytest.raises(TypeError):
        BaseRule()  # type: ignore[abstract]


def test_dummy_rule_inherits_base_attributes():
    """DummyRule hérite bien des attributs de base et peut les surcharger."""
    rule = DummyRule()

    assert rule.name == "DummyRule"
    assert rule.description == "Règle de test"
    assert rule.scope == RuleScope.DAY


def test_applies_to_returns_true_by_default():
    """Par défaut, applies_to() doit toujours renvoyer True quel que soit le contexte."""
    rule = DummyRule()
    assert rule.applies_to(None) is True
    assert rule.applies_to(object()) is True
    assert rule.applies_to({"anything": "goes"}) is True


def test_check_returns_bool_and_list_of_domain_alerts():
    """La méthode check() d'une règle concrète doit respecter la signature (bool, List[DomainAlert])."""
    rule = DummyRule()
    ok, alerts = rule.check(context={"foo": "bar"})

    assert isinstance(ok, bool)
    assert isinstance(alerts, list)
    assert all(isinstance(a, DomainAlert) for a in alerts)

    # Pour DummyRule, on sait ce qu'on renvoie
    assert ok is True
    assert len(alerts) == 1
    assert alerts[0].message == "Tout va bien"
    assert alerts[0].code == "DUMMY_OK"


def test_alert_helper_sets_common_fields():
    """_alert doit remplir correctement message, severity, jour, source et code."""
    rule = DummyRule()
    d = date(2025, 1, 1)

    alert = rule._alert(
        message="Message générique",
        severity=Severity.WARNING,
        jour=d,
        code="GENERIC",
    )

    assert isinstance(alert, DomainAlert)
    assert alert.message == "Message générique"
    assert alert.severity == Severity.WARNING
    assert alert.jour == d
    # source doit être le nom de la règle
    assert alert.source == "DummyRule"
    assert alert.code == "GENERIC"


def test_info_helper_builds_info_alert_with_source_and_code():
    rule = DummyRule()
    d = date(2025, 2, 2)

    alert = rule.info("Info message", jour=d, code="INFO_CODE")

    assert isinstance(alert, DomainAlert)
    assert alert.message == "Info message"
    assert alert.severity == Severity.INFO
    assert alert.jour == d
    assert alert.source == "DummyRule"
    assert alert.code == "INFO_CODE"


def test_warn_helper_builds_warning_alert():
    rule = DummyRule()

    alert = rule.warn("Warning message")

    assert isinstance(alert, DomainAlert)
    assert alert.message == "Warning message"
    assert alert.severity == Severity.WARNING
    # jour et code peuvent être None si non fournis
    assert alert.jour is None
    assert alert.code is None
    assert alert.source == "DummyRule"


def test_error_helper_builds_error_alert():
    rule = DummyRule()
    d = date(2025, 3, 3)

    alert = rule.error("Error message", jour=d, code="ERR42")

    assert isinstance(alert, DomainAlert)
    assert alert.message == "Error message"
    assert alert.severity == Severity.ERROR
    assert alert.jour == d
    assert alert.code == "ERR42"
    assert alert.source == "DummyRule"
