from datetime import date

import pytest

from core.rh_rules import RegimeB25ReposAnnuelRule
from core.utils.domain_alert import Severity
from core.domain.contexts.planning_context import PlanningContext


# ---------------------------------------------------------------------
# Fakes / stubs pour l'analyzer de repos
# ---------------------------------------------------------------------


class FakeReposSummary:
    def __init__(self, total_rp_days: int, total_rp_sundays: int):
        self.total_rp_days = total_rp_days
        self.total_rp_sundays = total_rp_sundays


class FakeReposAnalyzer:
    def __init__(self, total_rp_days: int, total_rp_sundays: int):
        self.summary = FakeReposSummary(total_rp_days, total_rp_sundays)
        self.calls = []

    def summarize_workdays(self, work_days):
        # On enregistre le nombre de WD vus pour vérifier la délégation
        self.calls.append(len(work_days))
        return self.summary


# ---------------------------------------------------------------------
# Applicabilité de la règle au régime B25 (regime_id = 1)
# ---------------------------------------------------------------------


def test_rule_not_applicable_if_regime_not_b25():
    """Si regime_id != 1, la règle est non applicable → (True, [])."""

    class DummyAgent:
        regime_id = 0  # pas B25

    class DummyContext:
        def __init__(self):
            self.agent = DummyAgent()

    ctx = DummyContext()
    fake_analyzer = FakeReposAnalyzer(0, 0)
    rule = RegimeB25ReposAnnuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []
    # YearRule.check ne doit pas tourner → aucun appel à l'analyzer
    assert fake_analyzer.calls == []


def test_rule_not_applicable_if_regime_missing():
    """Si regime_id est None/absent, la règle ne s'applique pas."""

    class DummyAgent:
        regime_id = None

    class DummyContext:
        def __init__(self):
            self.agent = DummyAgent()

    ctx = DummyContext()
    rule = RegimeB25ReposAnnuelRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []


# ---------------------------------------------------------------------
# Cas d'année vide
# ---------------------------------------------------------------------


def test_empty_year_produces_info_only(make_agent, make_workday):
    """
    Contexte couvrant plusieurs années, mais sans WorkDay pour une année donnée :
    on doit produire une INFO B25_ANNUEL_ANNEE_VIDE pour cette année.
    """
    agent = make_agent(regime_id=1)

    wd_2024 = make_workday(jour=date(2024, 6, 10), type_label="repos")
    wd_2026 = make_workday(jour=date(2026, 3, 5), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_2024, wd_2026],
        date_reference=wd_2024.jour,
    )
    # start_date = 2024-06-10, end_date = 2026-03-05 → années 2024, 2025, 2026 évaluées

    rule = RegimeB25ReposAnnuelRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]
    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "B25_ANNUEL_ANNEE_VIDE" in codes
    assert any("[2025]" in a.message for a in alerts if a.code == "B25_ANNUEL_ANNEE_VIDE")


# ---------------------------------------------------------------------
# Année partielle : contrôles non bloquants
# ---------------------------------------------------------------------


def test_partial_year_only_info(make_agent, make_workday):
    """
    Année civile partielle (is_full=False) :
    - la règle produit une synthèse + une info 'période partielle'
    - aucune erreur même si les repos sont sous les minima.
    """
    agent = make_agent(regime_id=1)

    # WD entre mars et octobre uniquement → année partielle
    wd_march = make_workday(jour=date(2025, 3, 1), type_label="repos")
    wd_oct = make_workday(jour=date(2025, 10, 31), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_march, wd_oct],
        date_reference=wd_march.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=10,    # largement < 114
        total_rp_sundays=5,  # largement < 30
    )
    rule = RegimeB25ReposAnnuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "B25_ANNUEL_SYNTHESIS" in codes
    assert "B25_ANNUEL_PERIODE_PARTIELLE" in codes

    assert any("période incomplète" in a.message.lower() for a in alerts)


# ---------------------------------------------------------------------
# Année complète : contrôles stricts
# ---------------------------------------------------------------------


def test_full_year_with_insufficient_rp_and_sundays(make_agent, make_workday):
    """
    Année civile complète (is_full=True) avec repos insuffisants :
      - erreurs sur RP annuels et dimanches.
    """
    agent = make_agent(regime_id=1)
    year = 2025

    wd_start = make_workday(jour=date(year, 1, 1), type_label="repos")
    wd_end = make_workday(jour=date(year, 12, 31), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_start, wd_end],
        date_reference=wd_start.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=50,     # < 114
        total_rp_sundays=10,  # < 30
    )
    rule = RegimeB25ReposAnnuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is False
    codes = {a.code for a in alerts}

    assert "B25_ANNUEL_SYNTHESIS" in codes
    assert "B25_ANNUEL_RP_INSUFFISANTS" in codes
    assert "B25_ANNUEL_DIMANCHES_INSUFFISANTS" in codes
    assert any(a.severity == Severity.ERROR for a in alerts)


def test_full_year_with_sufficient_rp_and_sundays(make_agent, make_workday):
    """
    Année civile complète (is_full=True) avec repos suffisants :
      - aucune erreur, uniquement des infos.
    """
    agent = make_agent(regime_id=1)
    year = 2026

    wd_start = make_workday(jour=date(year, 1, 1), type_label="repos")
    wd_end = make_workday(jour=date(year, 12, 31), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_start, wd_end],
        date_reference=wd_start.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=200,    # >= 114
        total_rp_sundays=40,  # >= 30
    )
    rule = RegimeB25ReposAnnuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "B25_ANNUEL_SYNTHESIS" in codes
    assert "B25_ANNUEL_RP_INSUFFISANTS" not in codes
    assert "B25_ANNUEL_DIMANCHES_INSUFFISANTS" not in codes


# ---------------------------------------------------------------------
# Cas PlanningContext sans work_days
# ---------------------------------------------------------------------


def test_no_workdays_returns_year_dates_missing_error(make_agent):
    """
    Si le contexte n'a aucun WorkDay avec un PlanningContext réel,
    YearRule ne peut pas déterminer start_date / end_date
    → erreur YEAR_DATES_MISSING.
    """
    agent = make_agent(regime_id=1)
    ctx = PlanningContext(
        agent=agent,
        work_days=[],
        date_reference=date(2025, 1, 1),
    )

    rule = RegimeB25ReposAnnuelRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]
    ok, alerts = rule.check(ctx)

    assert ok is False
    assert len(alerts) == 1
    a = alerts[0]
    assert a.severity == Severity.ERROR
    assert a.code == "YEAR_DATES_MISSING"
    assert "Impossible de déterminer les dates de début/fin" in a.message
