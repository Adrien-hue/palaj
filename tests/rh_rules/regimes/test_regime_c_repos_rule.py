from datetime import date

import pytest

from core.rh_rules import RegimeCReposRule
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
        # On enregistre le nombre de WD passés pour vérifier que la règle délègue bien
        self.calls.append(len(work_days))
        return self.summary


# ---------------------------------------------------------------------
# Applicabilité de la règle au régime C
# ---------------------------------------------------------------------


def test_rule_not_applicable_if_regime_not_c():
    """Si regime_id != 2, la règle est non applicable et doit retourner (True, [])."""

    class DummyAgent:
        regime_id = 1  # pas C

    class DummyContext:
        def __init__(self):
            self.agent = DummyAgent()

    ctx = DummyContext()
    fake_analyzer = FakeReposAnalyzer(0, 0)
    rule = RegimeCReposRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []
    # YearRule.check ne doit pas être appelé → aucun appel à l'analyzer
    assert fake_analyzer.calls == []


def test_rule_not_applicable_if_regime_missing():
    """Si regime_id est None (ou absent), la règle ne s'applique pas."""
    class DummyAgent:
        regime_id = None

    class DummyContext:
        def __init__(self):
            self.agent = DummyAgent()

    ctx = DummyContext()
    rule = RegimeCReposRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []


# ---------------------------------------------------------------------
# Cas d'années vides / multi-années
# ---------------------------------------------------------------------


def test_empty_year_produces_info_only(make_agent, make_workday):
    """
    Contexte couvrant 2024, 2025 et 2026, mais avec des WorkDay
    uniquement en 2024 et 2026 :
      - pour 2025, YearRule va appeler check_year avec work_days=[]
      - on doit obtenir une alerte INFO REGIME_C_EMPTY_YEAR pour 2025.
    """
    agent = make_agent(regime_id=2)

    wd_2024 = make_workday(jour=date(2024, 6, 10), type_label="repos")
    wd_2026 = make_workday(jour=date(2026, 3, 5), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_2024, wd_2026],
        date_reference=wd_2024.jour,
    )
    # start_date = 2024-06-10, end_date = 2026-03-05

    rule = RegimeCReposRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]
    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "REGIME_C_EMPTY_YEAR" in codes
    assert any("[2025]" in a.message for a in alerts if a.code == "REGIME_C_EMPTY_YEAR")


# ---------------------------------------------------------------------
# Année partielle : contrôles non bloquants
# ---------------------------------------------------------------------


def test_partial_year_only_info(make_agent, make_workday):
    """
    Année civile partielle (is_full=False) :
      - la règle produit une synthèse + une info 'partial year'
      - aucune erreur même si les repos sont sous les minima.
    """
    agent = make_agent(regime_id=2)

    # WD entre mars et octobre uniquement → année partielle
    wd_march = make_workday(jour=date(2025, 3, 1), type_label="repos")
    wd_oct = make_workday(jour=date(2025, 10, 31), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_march, wd_oct],
        date_reference=wd_march.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=10,     # largement sous les 118
        total_rp_sundays=5,   # largement sous les 52
    )
    rule = RegimeCReposRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "REGIME_C_REPOS_SYNTHESIS" in codes
    assert "REGIME_C_REPOS_PARTIAL_YEAR" in codes

    assert any("période incomplète" in a.message.lower() for a in alerts)


# ---------------------------------------------------------------------
# Année complète : contrôles stricts
# ---------------------------------------------------------------------


def test_full_year_with_insufficient_rp_and_sundays(make_agent, make_workday):
    """
    Année civile complète (is_full=True) avec repos insuffisants :
      - erreurs sur RP annuels et dimanches.
    """
    agent = make_agent(regime_id=2)
    year = 2025

    wd_start = make_workday(jour=date(year, 1, 1), type_label="repos")
    wd_end = make_workday(jour=date(year, 12, 31), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_start, wd_end],
        date_reference=wd_start.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=50,      # < 118
        total_rp_sundays=20,   # < 52
    )
    rule = RegimeCReposRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is False
    codes = {a.code for a in alerts}

    assert "REGIME_C_REPOS_SYNTHESIS" in codes
    assert "REGIME_C_REPOS_RP_INSUFFISANTS" in codes
    assert "REGIME_C_REPOS_DIMANCHES_INSUFFISANTS" in codes
    assert any(a.severity == Severity.ERROR for a in alerts)


def test_full_year_with_sufficient_rp_and_sundays(make_agent, make_workday):
    """
    Année civile complète (is_full=True) avec repos suffisants :
      - aucune erreur, uniquement des infos.
    """
    agent = make_agent(regime_id=2)
    year = 2026

    wd_start = make_workday(jour=date(year, 1, 1), type_label="repos")
    wd_end = make_workday(jour=date(year, 12, 31), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_start, wd_end],
        date_reference=wd_start.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=200,     # >= 118
        total_rp_sundays=80,   # >= 52
    )
    rule = RegimeCReposRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "REGIME_C_REPOS_SYNTHESIS" in codes
    assert "REGIME_C_REPOS_RP_INSUFFISANTS" not in codes
    assert "REGIME_C_REPOS_DIMANCHES_INSUFFISANTS" not in codes


# ---------------------------------------------------------------------
# Intégration basique avec un PlanningContext vide
# ---------------------------------------------------------------------


def test_no_workdays_returns_year_dates_missing_error(make_agent):
    """
    Si le contexte n'a aucun WorkDay avec un PlanningContext réel,
    YearRule ne peut pas déterminer start_date / end_date
    → erreur YEAR_DATES_MISSING (comportement identique à RegimeBReposRule).
    """
    agent = make_agent(regime_id=2)
    ctx = PlanningContext(
        agent=agent,
        work_days=[],
        date_reference=date(2025, 1, 1),
    )

    rule = RegimeCReposRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]
    ok, alerts = rule.check(ctx)

    assert ok is False
    assert len(alerts) == 1
    a = alerts[0]
    assert a.severity == Severity.ERROR
    assert a.code == "YEAR_DATES_MISSING"
    assert "Impossible de déterminer les dates de début/fin" in a.message
