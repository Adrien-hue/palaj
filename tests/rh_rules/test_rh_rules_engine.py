# tests/rh_rules/test_rh_rules_engine.py

import pytest
from datetime import date

from core.rh_rules.rh_rules_engine import RHRulesEngine
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.contexts.planning_context import PlanningContext


# --- Fixtures & Mocks ----------------------------------------------------------


@pytest.fixture
def fake_context(make_agent, make_workday):
    """
    Contexte minimal avec 3 jours travaillés.
    On utilise les factories partagées pour rester cohérent avec le reste de la suite.
    """
    agent = make_agent()

    wd1 = make_workday(jour=date(2025, 1, 1), type_label="poste", agent=agent)
    wd2 = make_workday(jour=date(2025, 1, 2), type_label="poste", agent=agent)
    wd3 = make_workday(jour=date(2025, 1, 3), type_label="poste", agent=agent)

    ctx = PlanningContext(agent=agent, work_days=[wd1, wd2, wd3])
    return ctx


class FakeRule(BaseRule):
    """Règle simulée pour tester le moteur RH."""

    def __init__(self, name, scope, alerts=None):
        super().__init__()
        self.name = name
        self.scope = scope
        self._alerts = alerts or []
        self.called = 0

    def check(self, context):
        self.called += 1
        # Simplement renvoyer les alertes pré-configurées
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


def test_run_for_context_empty(make_agent):
    engine = RHRulesEngine()
    ctx = PlanningContext(agent=make_agent(), work_days=[])
    is_valid, alerts = engine.run_for_context(ctx)

    assert is_valid
    assert alerts == []


def test_run_for_context_with_day_rules(fake_context):
    # Une règle "jour" avec une alerte de warning
    rule = FakeRule(
        "Jour Rule",
        RuleScope.DAY,
        alerts=[
            DomainAlert(
                "Attention RH",
                Severity.WARNING,
                date(2025, 1, 1),
                "FakeRule",
            )
        ],
    )

    engine = RHRulesEngine(rules=[rule])
    is_valid, alerts = engine.run_for_context(fake_context)

    # Appel 3 fois (pour 3 jours)
    assert rule.called == 3
    assert len(alerts) == 3
    assert all(a.message == "Attention RH" for a in alerts)
    # pas d’erreur bloquante → is_valid = True
    assert is_valid


def test_run_for_context_with_period_rule(fake_context):
    rule_period = FakeRule(
        "Period Rule",
        RuleScope.PERIOD,
        alerts=[
            DomainAlert(
                "Erreur GPT",
                Severity.ERROR,
                None,
                "FakeRule",
            )
        ],
    )

    engine = RHRulesEngine(rules=[rule_period])
    is_valid, alerts = engine.run_for_context(fake_context)

    assert rule_period.called == 1  # exécutée une seule fois
    assert len(alerts) == 1
    assert not is_valid  # contient une erreur bloquante


def test_mix_day_and_period_rules(fake_context):
    day_rule = FakeRule("DayRule", RuleScope.DAY)
    period_rule = FakeRule("PeriodRule", RuleScope.PERIOD)

    engine = RHRulesEngine(rules=[day_rule, period_rule])
    engine.run_for_context(fake_context)

    assert day_rule.called == 3
    assert period_rule.called == 1