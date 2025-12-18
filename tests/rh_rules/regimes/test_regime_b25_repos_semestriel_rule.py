from datetime import date

import pytest

from core.rh_rules import RegimeB25ReposSemestrielRule
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
# Applicabilité (régime B25)
# ---------------------------------------------------------------------


def test_rule_not_applicable_if_regime_not_b25():
    """Si regime_id != 1, la règle est non applicable → (True, [])."""

    class DummyAgent:
        regime_id = 0

    class DummyContext:
        def __init__(self):
            self.agent = DummyAgent()

    ctx = DummyContext()
    fake_analyzer = FakeReposAnalyzer(0, 0)
    rule = RegimeB25ReposSemestrielRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []
    assert fake_analyzer.calls == []  # pas d'appel à summarize_workdays


def test_rule_not_applicable_if_regime_missing():
    """Si regime_id est None/absent, la règle ne s'applique pas."""

    class DummyAgent:
        regime_id = None

    class DummyContext:
        def __init__(self):
            self.agent = DummyAgent()

    ctx = DummyContext()
    rule = RegimeB25ReposSemestrielRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []


# ---------------------------------------------------------------------
# Semestres vides
# ---------------------------------------------------------------------


def test_empty_semester_produces_info_only(make_agent, make_workday):
    """
    Contexte couvrant plusieurs semestres, avec au moins un semestre sans aucun WorkDay :
    on doit obtenir une alerte INFO B25_SEMESTRE_VIDE pour ce semestre.
    """
    agent = make_agent(regime_id=1)

    # WD en 2024-S1 et 2025-S2, rien en 2025-S1
    wd_2024_s1 = make_workday(jour=date(2024, 3, 10), type_label="repos")
    wd_2025_s2 = make_workday(jour=date(2025, 9, 5), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_2024_s1, wd_2025_s2],
        date_reference=wd_2024_s1.jour,
    )

    rule = RegimeB25ReposSemestrielRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]
    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "B25_SEMESTRE_VIDE" in codes
    # On s'assure qu'au moins un message mentionne bien un semestre comme "vide"
    assert any("aucun jour planifié" in a.message.lower() for a in alerts)


# ---------------------------------------------------------------------
# Semestre partiel : contrôles non bloquants
# ---------------------------------------------------------------------


def test_partial_semester_only_info(make_agent, make_workday):
    """
    Semestre partiellement couvert (is_full=False) :
    - synthèse + info 'semestre partiel'
    - aucune erreur même si nb RP < MIN_RP_SEMESTRE.
    """
    agent = make_agent(regime_id=1)

    # S1 2025 : semestre complet = 01/01 → 30/06
    # On ne couvre qu'une partie : mars → avril
    wd_march = make_workday(jour=date(2025, 3, 1), type_label="repos")
    wd_april = make_workday(jour=date(2025, 4, 30), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_march, wd_april],
        date_reference=wd_march.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=10,    # < 56
        total_rp_sundays=3,  # valeur non utilisée ici, mais peu importe
    )
    rule = RegimeB25ReposSemestrielRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "B25_SEMESTRE_SYNTHESIS" in codes
    assert "B25_SEMESTRE_PARTIEL" in codes

    assert any("semestre partiellement couvert" in a.message.lower() for a in alerts)


# ---------------------------------------------------------------------
# Semestre complet : contrôles stricts
# ---------------------------------------------------------------------


def test_full_semester_with_insufficient_rp(make_agent, make_workday):
    """
    Semestre civil complet (is_full=True) avec RP insuffisants :
      - erreur B25_SEMESTRE_RP_INSUFFISANTS attendue.
    """
    agent = make_agent(regime_id=1)
    year = 2025

    # S1 : 01/01 → 30/06
    wd_start = make_workday(jour=date(year, 1, 1), type_label="repos")
    wd_end = make_workday(jour=date(year, 6, 30), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_start, wd_end],
        date_reference=wd_start.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=30,    # < 56
        total_rp_sundays=5,  # quelconque
    )
    rule = RegimeB25ReposSemestrielRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is False
    codes = {a.code for a in alerts}

    assert "B25_SEMESTRE_SYNTHESIS" in codes
    assert "B25_SEMESTRE_RP_INSUFFISANTS" in codes
    assert any(a.severity == Severity.ERROR for a in alerts)


def test_full_semester_with_sufficient_rp(make_agent, make_workday):
    """
    Semestre civil complet (is_full=True) avec RP suffisants :
      - aucune erreur, uniquement des infos.
    """
    agent = make_agent(regime_id=1)
    year = 2025

    wd_start = make_workday(jour=date(year, 1, 1), type_label="repos")
    wd_end = make_workday(jour=date(year, 6, 30), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_start, wd_end],
        date_reference=wd_start.jour,
    )

    fake_analyzer = FakeReposAnalyzer(
        total_rp_days=80,    # >= 56
        total_rp_sundays=10,
    )
    rule = RegimeB25ReposSemestrielRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "B25_SEMESTRE_SYNTHESIS" in codes
    assert "B25_SEMESTRE_RP_INSUFFISANTS" not in codes


# ---------------------------------------------------------------------
# Cas PlanningContext sans work_days
# ---------------------------------------------------------------------


def test_no_workdays_returns_semester_dates_missing_error(make_agent):
    """
    Si le contexte n'a aucun WorkDay avec un PlanningContext réel,
    SemesterRule ne peut pas déterminer start_date / end_date
    → erreur SEMESTER_DATES_MISSING.
    """
    agent = make_agent(regime_id=1)
    ctx = PlanningContext(
        agent=agent,
        work_days=[],
        date_reference=date(2025, 1, 1),
    )

    rule = RegimeB25ReposSemestrielRule(analyzer=FakeReposAnalyzer(0, 0)) # pyright: ignore[reportArgumentType]
    ok, alerts = rule.check(ctx)

    assert ok is False
    assert len(alerts) == 1
    a = alerts[0]
    assert a.severity == Severity.ERROR
    assert a.code == "SEMESTER_DATES_MISSING"
    assert "Impossible de déterminer les dates de début/fin" in a.message
