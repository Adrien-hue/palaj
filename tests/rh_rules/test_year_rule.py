from datetime import date

import pytest

from core.rh_rules.year_rule import YearRule
from core.utils.domain_alert import Severity
from core.domain.contexts.planning_context import PlanningContext


# ---------------------------------------------------------------------
# Implémentations concrètes de test
# ---------------------------------------------------------------------


class DummyYearRule(YearRule):
    """
    Règle annuelle de test :
    - enregistre tous les appels à check_year
    - renvoie une alerte INFO pour chaque année traitée
    """

    name = "DummyYearRule"

    def __init__(self):
        super().__init__()
        self.calls: list[tuple[int, date, date, bool, int]] = []

    def check_year(
        self,
        context,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        work_days,
    ):
        # on logge : (year, year_start, year_end, is_full, nb_workdays)
        self.calls.append((year, year_start, year_end, is_full, len(work_days)))
        alert = self.info(
            msg=f"Year {year}, full={is_full}, nb_wd={len(work_days)}",
            code="DUMMY_YEAR_INFO",
        )
        return True, [alert]


class ErrorYearRule(YearRule):
    """
    Règle de test qui produit une erreur sur une année précise.
    """

    def __init__(self, error_year: int):
        super().__init__()
        self.error_year = error_year
        self.calls: list[tuple[int, bool]] = []

    def check_year(
        self,
        context,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        work_days,
    ):
        self.calls.append((year, is_full))
        if year == self.error_year:
            alert = self.error(
                msg=f"Erreur sur {year}",
                code="YEAR_ERROR_TEST",
            )
            return False, [alert]
        else:
            return True, [self.info(f"OK {year}")]


class RecordingYearRule(YearRule):
    """
    Règle qui enregistre précisément quels jours sont passés pour chaque année.
    """

    def __init__(self):
        super().__init__()
        self.calls: list[dict] = []

    def check_year(
        self,
        context,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        work_days,
    ):
        self.calls.append(
            {
                "year": year,
                "is_full": is_full,
                "jours": sorted([wd.jour for wd in work_days]),
            }
        )
        return True, []


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_year_rule_is_abstract():
    """YearRule ne doit pas être instanciable directement."""
    with pytest.raises(TypeError):
        YearRule()  # type: ignore[abstract]


def test_check_dates_missing_returns_error():
    """
    Si start_date ou end_date manquent → erreur YEAR_DATES_MISSING.
    On utilise un contexte factice minimal avec start/end à None.
    """

    class ContextNoDates:
        start_date = None
        end_date = None
        work_days = [1]  # n'importe quoi, on ne va pas plus loin

    ctx = ContextNoDates()
    rule = DummyYearRule()

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is False
    assert len(alerts) == 1
    a = alerts[0]
    assert a.severity == Severity.ERROR
    assert a.code == "YEAR_DATES_MISSING"
    assert "Impossible de déterminer les dates de début/fin" in a.message


def test_check_no_workdays_returns_true_and_no_alerts():
    """
    Si le contexte ne contient aucun work_day, on doit retourner (True, [])
    dès lors que start_date / end_date sont renseignées.
    """

    class EmptyContext:
        start_date = date(2025, 1, 1)
        end_date = date(2025, 12, 31)
        work_days = []

    ctx = EmptyContext()
    rule = DummyYearRule()

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []


def test_check_calls_check_year_for_each_overlapping_year(make_context):
    """
    Contexte couvrant plusieurs années :
    - on doit appeler check_year pour chaque année couverte,
    - is_full doit être False si le contexte ne couvre pas l'année entière.
    """
    # Contexte qui commence le 1er juin 2025, sur 400 jours -> jusque courant 2026
    ctx = make_context(
        nb_jours=400,
        start_date=date(2025, 6, 1),
        include_left_repos=True,
        include_right_repos=True,
    )
    # ctx.start_date ~ 2025-06-01, ctx.end_date ~ 2026-07/08

    rule = DummyYearRule()
    ok, alerts = rule.check(ctx)

    assert ok is True

    # On a au moins 2 années : 2025 et 2026
    years_called = {year for (year, _, _, _, _) in rule.calls}
    assert 2025 in years_called
    assert 2026 in years_called

    # is_full doit être False pour les deux (le contexte ne couvre pas 1/1→31/12)
    for year, year_start, year_end, is_full, _ in rule.calls:
        if year in (2025, 2026):
            assert is_full is False

    # Toutes les alertes sont INFO issues de DummyYearRule
    assert all(a.severity == Severity.INFO for a in alerts)
    assert all(a.code == "DUMMY_YEAR_INFO" for a in alerts)


def test_full_year_marks_is_full_true(make_agent, make_workday):
    """
    Si le contexte couvre exactement une année complète (01/01 → 31/12),
    is_full doit être True pour cette année.
    """
    from core.domain.entities import Agent

    year = 2025
    wd1 = make_workday(jour=date(year, 1, 1), type_label="poste")
    wd2 = make_workday(jour=date(year, 12, 31), type_label="poste")

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd1, wd2],
        date_reference=date(year, 1, 1),
    )
    # start_date = 2025-01-01, end_date = 2025-12-31

    rule = DummyYearRule()
    ok, _ = rule.check(context)

    assert ok is True
    assert len(rule.calls) == 1

    year_called, year_start, year_end, is_full, nb_wd = rule.calls[0]
    assert year_called == year
    assert year_start == date(year, 1, 1)
    assert year_end == date(year, 12, 31)
    assert is_full is True
    # les deux work_days sont dans cette année
    assert nb_wd == 2


def test_workdays_are_correctly_dispatched_per_year(make_agent, make_workday):
    """
    Vérifie que les work_days sont correctement dispatchés par année :

    - Un WD en 2024 doit apparaître uniquement dans l'année 2024.
    - Un WD en 2025 uniquement dans l'année 2025.
    """
    wd_2024 = make_workday(jour=date(2024, 6, 10), type_label="poste")
    wd_2025 = make_workday(jour=date(2025, 3, 5), type_label="poste")

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd_2024, wd_2025],
        date_reference=wd_2024.jour,
    )
    # start_date = 2024-06-10, end_date = 2025-03-05

    rule = RecordingYearRule()
    ok, alerts = rule.check(context)

    assert ok is True
    assert alerts == []

    calls = {c["year"]: c for c in rule.calls}

    assert 2024 in calls
    assert 2025 in calls

    c2024 = calls[2024]
    c2025 = calls[2025]

    assert c2024["jours"] == [wd_2024.jour]
    assert c2025["jours"] == [wd_2025.jour]


def test_check_returns_false_if_any_year_has_error(make_context):
    """
    Si une année retourne ok=False avec une alerte ERROR,
    le résultat global doit être ok=False.
    """
    # Contexte qui couvre largement 2025 (et un peu ailleurs)
    ctx = make_context(
        nb_jours=400,
        start_date=date(2025, 1, 1),
        include_left_repos=True,
        include_right_repos=True,
    )

    rule = ErrorYearRule(error_year=2025)

    ok, alerts = rule.check(ctx)

    # On a au moins une entrée pour 2025
    years_called = {year for (year, _) in rule.calls}
    assert 2025 in years_called

    # Résultat global invalide
    assert ok is False
    severities = {a.severity for a in alerts}
    assert Severity.ERROR in severities
    assert any(a.code == "YEAR_ERROR_TEST" for a in alerts)
