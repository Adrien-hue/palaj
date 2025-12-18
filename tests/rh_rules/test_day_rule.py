import pytest
from datetime import date

from core.rh_rules.day_rule import DayRule
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import Agent
from core.domain.models.work_day import WorkDay


# ---------------------------------------------------------------------
# Implémentation concrète minimale pour tester DayRule
# ---------------------------------------------------------------------

class DummyDayRule(DayRule):
    """
    Règle journalière minimale pour les tests.
    Elle renvoie toujours ok=True + une alerte info.
    """

    name = "DummyDayRule"
    description = "Test rule"

    def check_day(self, context, work_day):
        return True, [
            self.info(
                f"WorkDay OK: {work_day.jour}",
                jour=work_day.jour,
                code="DUMMY_DAY_OK",
            )
        ]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def make_context_with_day(work_day):
    """
    Construit un PlanningContext minimal contenant current_work_day.
    """
    agent = Agent(id=1, nom="Test", prenom="Agent")
    return PlanningContext(
        agent=agent,
        work_days=[work_day],
        date_reference=work_day.jour,
        current_work_day=work_day,
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_day_rule_is_abstract():
    """DayRule ne doit pas être instanciable directement."""
    with pytest.raises(TypeError):
        DayRule()  # type: ignore[abstract]


def test_day_rule_check_requires_current_work_day():
    """
    Si current_work_day n’est pas présent dans le contexte,
    check() doit renvoyer une erreur explicite.
    """
    agent = Agent(id=1, nom="Test", prenom="Agent")
    context = PlanningContext(
        agent=agent,
        work_days=[],
        current_work_day=None,   # important
    )

    rule = DummyDayRule()
    ok, alerts = rule.check(context)

    assert ok is False
    assert len(alerts) == 1
    alert = alerts[0]

    assert alert.severity == Severity.ERROR
    assert "Impossible de déterminer le WorkDay" in alert.message
    assert alert.code == "DAY_NO_WORKDAY_REFERENCE"


def test_day_rule_delegates_to_check_day():
    """check() doit déléguer correctement à check_day()."""

    wd = WorkDay(jour=date(2025, 1, 2), etat=None, tranches=[])
    context = make_context_with_day(wd)

    rule = DummyDayRule()
    ok, alerts = rule.check(context)

    assert ok is True
    assert len(alerts) == 1
    alert = alerts[0]

    assert alert.code == "DUMMY_DAY_OK"
    assert alert.jour == wd.jour
    assert "WorkDay OK" in alert.message


def test_day_rule_scope_is_day():
    """DayRule doit imposer scope=DAY pour toutes ses sous-classes."""
    rule = DummyDayRule()
    assert rule.scope.value == "day"
