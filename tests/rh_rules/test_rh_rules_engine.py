import pytest
from datetime import date
from types import SimpleNamespace

from core.rh_rules.rh_rules_engine import RHRulesEngine
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities.work_day import WorkDay


# --- Fixtures & Mocks ----------------------------------------------------------

@pytest.fixture
def fake_context():
    """Contexte minimal avec 3 jours travaillés"""
    wd1 = WorkDay(jour=date(2025, 1, 1))
    wd2 = WorkDay(jour=date(2025, 1, 2))
    wd3 = WorkDay(jour=date(2025, 1, 3))
    ctx = PlanningContext(agent=SimpleNamespace(id=1), work_days=[wd1, wd2, wd3])
    return ctx


class FakeRule(BaseRule):
    """Règle simulée pour test."""
    def __init__(self, name, scope, alerts=None):
        super().__init__()
        self.name = name
        self.scope = scope
        self._alerts = alerts or []
        self.called = 0

    def check(self, context):
        self.called += 1
        return True, self._alerts


# --- Tests ---------------------------------------------------------------------

def test_register_and_list_rules():
    rule = FakeRule("Test Rule", RuleScope.DAY)
    engine = RHRulesEngine()
    engine.register_rule(rule)

    names = engine.list_rules()
    assert len(names) == 1
    assert "Test Rule" in names[0]
    assert "DAY" in names[0]


def test_run_for_context_empty():
    engine = RHRulesEngine()
    ctx = PlanningContext(agent=SimpleNamespace(id=1), work_days=[])
    is_valid, alerts = engine.run_for_context(ctx)

    assert is_valid
    assert alerts == []


def test_run_for_context_with_day_rules(fake_context):
    # Une règle "jour" avec une alerte de warning
    rule = FakeRule(
        "Jour Rule",
        RuleScope.DAY,
        alerts=[DomainAlert("Attention RH", Severity.WARNING, date(2025, 1, 1), "FakeRule")]
    )

    engine = RHRulesEngine(rules=[rule], verbose=False)
    is_valid, alerts = engine.run_for_context(fake_context)

    # Appel 3 fois (pour 3 jours)
    assert rule.called == 3
    assert len(alerts) == 3
    assert all(a.message == "Attention RH" for a in alerts)
    assert is_valid  # pas d’erreur bloquante


def test_run_for_context_with_period_rule(fake_context):
    rule_period = FakeRule(
        "Period Rule",
        RuleScope.PERIOD,
        alerts=[DomainAlert("Erreur GPT", Severity.ERROR, None, "FakeRule")]
    )

    engine = RHRulesEngine(rules=[rule_period], verbose=False)
    is_valid, alerts = engine.run_for_context(fake_context)

    assert rule_period.called == 1  # exécutée une seule fois
    assert len(alerts) == 1
    assert not is_valid  # contient une erreur bloquante


def test_mix_day_and_period_rules(fake_context):
    day_rule = FakeRule("DayRule", RuleScope.DAY)
    period_rule = FakeRule("PeriodRule", RuleScope.PERIOD)

    engine = RHRulesEngine(rules=[day_rule, period_rule], verbose=False)
    engine.run_for_context(fake_context)

    assert day_rule.called == 3
    assert period_rule.called == 1


def test_print_summary_report(capsys):
    alerts = [
        DomainAlert("Test info", Severity.INFO, None, "X"),
        DomainAlert("Test warn", Severity.WARNING, None, "Y"),
        DomainAlert("Test error", Severity.ERROR, None, "Z"),
    ]
    engine = RHRulesEngine(verbose=True)
    engine._print_summary_report(False, alerts)

    out = capsys.readouterr().out
    assert "Test error" in out
    assert "Des non-conformités" in out

    # Test silent mode
    engine.verbose = False
    engine._print_summary_report(True, alerts)  # ne doit rien afficher
    out2 = capsys.readouterr().out
    assert out2 == ""
