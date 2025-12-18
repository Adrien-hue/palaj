from datetime import date, timedelta

import pytest

from core.rh_rules import RegimeB25ReposMensuelRule
from core.utils.domain_alert import Severity
from core.domain.contexts.planning_context import PlanningContext


# ---------------------------------------------------------------------
# Fakes pour ReposStatsAnalyzer
# ---------------------------------------------------------------------


class FakePeriodeRepos:
    def __init__(self, start: date, nb_jours: int, is_rpsd: bool):
        self.start = start
        self.nb_jours = nb_jours
        self.end = start + timedelta(days=nb_jours - 1)
        self._is_rpsd = is_rpsd

    def is_rpsd(self) -> bool:
        return self._is_rpsd


class FakeReposSummary:
    def __init__(self, total_rp_days: int, periodes: list[FakePeriodeRepos]):
        self.total_rp_days = total_rp_days
        self.total_rp_sundays = 0
        self.periodes = periodes


class FakeReposAnalyzer:
    def __init__(self, summary: FakeReposSummary):
        self.summary = summary
        self.calls = 0

    def summarize_workdays(self, work_days):
        self.calls += 1
        return self.summary


# ---------------------------------------------------------------------
# Applicabilité / check global
# ---------------------------------------------------------------------


def test_rule_not_applicable_if_regime_not_b25():
    """Si regime_id != 1, la règle est non applicable → (True, [])."""

    class DummyAgent:
        regime_id = 0

    class DummyContext:
        def __init__(self):
            self.agent = DummyAgent()
            # pas besoin de work_days : on est court-circuité avant

    ctx = DummyContext()
    fake_analyzer = FakeReposAnalyzer(
        FakeReposSummary(total_rp_days=10, periodes=[])
    )
    rule = RegimeB25ReposMensuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []
    assert fake_analyzer.calls == 0


def test_rule_not_applicable_if_regime_missing():
    """Si regime_id est None/absent, la règle ne s'applique pas."""

    class DummyAgent:
        regime_id = None

    class DummyContext:
        def __init__(self):
            self.agent = DummyAgent()

    ctx = DummyContext()
    rule = RegimeB25ReposMensuelRule(analyzer=FakeReposAnalyzer(FakeReposSummary(0, []))) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []


def test_check_b25_with_no_workdays_returns_true_and_no_alerts(make_agent):
    """
    Pour un agent B25 mais sans work_days, la règle court-circuitée dans check()
    doit retourner (True, []) sans passer par MonthRule.
    """
    agent = make_agent(regime_id=1)
    ctx = PlanningContext(
        agent=agent,
        work_days=[],
        date_reference=date(2025, 1, 1),
    )

    fake_analyzer = FakeReposAnalyzer(FakeReposSummary(0, []))
    rule = RegimeB25ReposMensuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert alerts == []
    assert fake_analyzer.calls == 0


# ---------------------------------------------------------------------
# Mois partiels
# ---------------------------------------------------------------------


def test_partial_month_with_repos_produces_info_only(make_agent, make_workday):
    """
    Mois partiel (is_full=False) avec des RP :
     - aucune erreur,
     - une alerte INFO B25_MOIS_PARTIEL.
    """
    agent = make_agent(regime_id=1)

    # Un seul jour de repos en plein milieu du mois → mois partiel (start_date > 1er)
    wd = make_workday(jour=date(2025, 1, 15), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd],
        date_reference=wd.jour,
    )

    summary = FakeReposSummary(
        total_rp_days=5,
        periodes=[],
    )
    fake_analyzer = FakeReposAnalyzer(summary)
    rule = RegimeB25ReposMensuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert all(a.severity != Severity.ERROR for a in alerts)

    codes = {a.code for a in alerts}
    assert "B25_MOIS_PARTIEL" in codes
    assert any("suivi mensuel" in a.message.lower() for a in alerts)


def test_partial_month_with_no_repos_produces_no_alert(make_agent, make_workday):
    """
    Mois partiel (is_full=False) mais pas de jours de repos (total_rp_days=0) :
     - aucun message, aucun contrôle.
    """
    agent = make_agent(regime_id=1)

    # Jour de travail uniquement dans le mois
    wd = make_workday(jour=date(2025, 1, 10), type_label="poste")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd],
        date_reference=wd.jour,
    )

    summary = FakeReposSummary(
        total_rp_days=0,
        periodes=[],
    )
    fake_analyzer = FakeReposAnalyzer(summary)
    rule = RegimeB25ReposMensuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    # aucun repos dans le résumé → pas d'alerte B25_MOIS_PARTIEL
    assert alerts == []


# ---------------------------------------------------------------------
# Mois complets : contrôles stricts
# ---------------------------------------------------------------------


def test_full_month_with_sufficient_rpsd_and_rp2plus(make_agent, make_workday):
    """
    Mois civil complet (is_full=True) avec :
     - au moins 1 RPSD,
     - au moins 2 périodes de repos de 2+ jours.
    → OK, uniquement une synthèse INFO.
    """
    agent = make_agent(regime_id=1)
    year = 2025
    month = 1

    # Pour que le mois soit vu comme complet :
    #  - start_date = 1er janvier
    #  - end_date = 31 janvier
    wd_start = make_workday(jour=date(year, month, 1), type_label="poste")
    wd_end = make_workday(jour=date(year, month, 31), type_label="poste")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_start, wd_end],
        date_reference=wd_start.jour,
    )

    month_start = date(year, month, 1)

    # On fabrique 2 périodes de 2+ jours dont 1 RPSD
    periodes = [
        FakePeriodeRepos(start=month_start + timedelta(days=4), nb_jours=2, is_rpsd=True),
        FakePeriodeRepos(start=month_start + timedelta(days=10), nb_jours=3, is_rpsd=False),
    ]
    summary = FakeReposSummary(
        total_rp_days=10,
        periodes=periodes,
    )
    fake_analyzer = FakeReposAnalyzer(summary)

    rule = RegimeB25ReposMensuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]
    ok, alerts = rule.check(ctx)

    assert ok is True
    # On doit avoir au moins la synthèse
    codes = {a.code for a in alerts}
    assert "B25_MOIS_SYNTHESIS" in codes
    # Pas de non-conformité
    assert "B25_MOIS_NON_CONFORME" not in codes
    assert all(a.severity != Severity.ERROR for a in alerts)


def test_full_month_with_insufficient_rpsd_or_rp2plus(make_agent, make_workday):
    """
    Mois civil complet (is_full=True) mais :
     - aucun RPSD
     - une seule période de repos de 2+ jours
    → erreur B25_MOIS_NON_CONFORME.
    """
    agent = make_agent(regime_id=1)
    year = 2025
    month = 1

    wd_start = make_workday(jour=date(year, month, 1), type_label="poste")
    wd_end = make_workday(jour=date(year, month, 31), type_label="poste")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_start, wd_end],
        date_reference=wd_start.jour,
    )

    month_start = date(year, month, 1)

    # 1 seule période de 2 jours, non RPSD → RPSD=0, RP2+=1
    periodes = [
        FakePeriodeRepos(start=month_start + timedelta(days=3), nb_jours=2, is_rpsd=False),
    ]

    summary = FakeReposSummary(
        total_rp_days=4,
        periodes=periodes,
    )
    fake_analyzer = FakeReposAnalyzer(summary)
    rule = RegimeB25ReposMensuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is False
    codes = {a.code for a in alerts}
    assert "B25_MOIS_SYNTHESIS" in codes
    assert "B25_MOIS_NON_CONFORME" in codes
    assert any(a.severity == Severity.ERROR for a in alerts)


# ---------------------------------------------------------------------
# Dispatch des mois / work_days
# ---------------------------------------------------------------------


def test_month_without_workdays_in_context_is_ignored(make_agent, make_workday):
    """
    Contexte couvrant plusieurs mois mais avec des WorkDay seulement en janvier et avril.
    On vérifie que :
      - check_month est appelé pour les mois qui ont un overlap
      - l'analyzer n'est appelé que pour les mois où il y a des work_days (janvier & avril)
    """

    agent = make_agent(regime_id=1)

    wd_jan = make_workday(jour=date(2025, 1, 10), type_label="repos")
    wd_apr = make_workday(jour=date(2025, 4, 5), type_label="repos")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_jan, wd_apr],
        date_reference=wd_jan.jour,
    )
    # start_date = 2025-01-10, end_date = 2025-04-05
    # Mois considérés : janvier, février, mars, avril
    # WorkDays : uniquement en janvier et avril

    summary = FakeReposSummary(
        total_rp_days=1,
        periodes=[],
    )
    fake_analyzer = FakeReposAnalyzer(summary)
    rule = RegimeB25ReposMensuelRule(analyzer=fake_analyzer) # pyright: ignore[reportArgumentType]

    ok, alerts = rule.check(ctx)

    assert ok is True
    # summarize_workdays doit avoir été appelé pour janvier et avril uniquement
    assert fake_analyzer.calls == 2

    # Pas d'erreur attendue dans ce scénario
    assert all(a.severity != Severity.ERROR for a in alerts)
