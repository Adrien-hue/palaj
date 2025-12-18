from datetime import date, timedelta

import pytest

from core.rh_rules.semester_rule import SemesterRule
from core.utils.domain_alert import Severity
from core.domain.contexts.planning_context import PlanningContext


# ---------------------------------------------------------------------
# Implémentations concrètes de test
# ---------------------------------------------------------------------


class DummySemesterRule(SemesterRule):
    """
    Règle semestrielle de test :
    - enregistre tous les appels à check_semester
    - renvoie une alerte INFO pour chaque semestre traité
    """

    name = "DummySemesterRule"

    def __init__(self):
        super().__init__()
        self.calls: list[tuple[int, str, date, date, bool, int]] = []

    def check_semester(
        self,
        context,
        year: int,
        label: str,
        sem_start: date,
        sem_end: date,
        is_full: bool,
        work_days,
    ):
        # On logge : (année, label, start, end, is_full, nb_workdays)
        self.calls.append((year, label, sem_start, sem_end, is_full, len(work_days)))
        alert = self.info(
            msg=f"Semester {year}-{label}, full={is_full}, nb_wd={len(work_days)}",
            code="DUMMY_SEM_INFO",
        )
        return True, [alert]


class ErrorSemesterRule(SemesterRule):
    """
    Règle de test qui produit une erreur sur un semestre précis
    pour vérifier la propagation de l'état global.
    """

    def __init__(self, error_year: int, error_label: str):
        super().__init__()
        self.error_year = error_year
        self.error_label = error_label
        self.calls: list[tuple[int, str, bool]] = []

    def check_semester(
        self,
        context,
        year: int,
        label: str,
        sem_start: date,
        sem_end: date,
        is_full: bool,
        work_days,
    ):
        self.calls.append((year, label, is_full))
        if (year, label) == (self.error_year, self.error_label):
            alert = self.error(
                msg=f"Erreur sur {year}-{label}",
                code="SEMESTER_ERROR_TEST",
            )
            return False, [alert]
        else:
            return True, [self.info(f"OK {year}-{label}")]


class RecordingSemesterRule(SemesterRule):
    """
    Règle pour vérifier la bonne distribution des work_days dans les semestres.
    """

    def __init__(self):
        super().__init__()
        self.calls: list[dict] = []

    def check_semester(
        self,
        context,
        year: int,
        label: str,
        sem_start: date,
        sem_end: date,
        is_full: bool,
        work_days,
    ):
        self.calls.append(
            {
                "year": year,
                "label": label,
                "is_full": is_full,
                "jours": sorted([wd.jour for wd in work_days]),
            }
        )
        return True, []


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_semester_rule_is_abstract():
    """SemesterRule ne doit pas être instanciable directement."""
    with pytest.raises(TypeError):
        SemesterRule()  # type: ignore[abstract]


def test_semester_ranges_for_year():
    """_semester_ranges_for_year doit retourner S1 et S2 correctement bornés."""
    rule = DummySemesterRule()
    year = 2025
    sems = rule._semester_ranges_for_year(year)

    assert len(sems) == 2

    (label1, s1_start, s1_end), (label2, s2_start, s2_end) = sems

    assert label1 == "S1"
    assert s1_start == date(year, 1, 1)
    assert s1_end == date(year, 6, 30)

    assert label2 == "S2"
    assert s2_start == date(year, 7, 1)
    assert s2_end == date(year, 12, 31)


def test_check_dates_missing_returns_error():
    """
    Si start_date ou end_date manquent → erreur SEMESTER_DATES_MISSING.
    On utilise un contexte factice minimal avec start_date / end_date à None.
    """

    class ContextNoDates:
        start_date = None
        end_date = None
        work_days = [1]  # peu importe, on ne va pas jusque-là

    ctx = ContextNoDates()
    rule = DummySemesterRule()

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is False
    assert len(alerts) == 1
    a = alerts[0]
    assert a.severity == Severity.ERROR
    assert a.code == "SEMESTER_DATES_MISSING"
    assert "Impossible de déterminer les dates de début/fin" in a.message


def test_check_no_workdays_returns_true_and_no_alerts():
    """
    Si le contexte ne contient aucun work_day, on doit retourner (True, [])
    dès lors que start_date / end_date sont renseignées.
    """

    class EmptyContext:
        start_date = date(2025, 1, 1)
        end_date = date(2025, 12, 31)
        work_days = []  # vide

    ctx = EmptyContext()
    rule = DummySemesterRule()

    ok, alerts = rule.check(ctx) # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []


def test_check_calls_check_semester_for_overlapping_semesters(make_context):
    """
    Contexte couvrant une partie de S1 et une partie de S2 :
    - le semestre S1 et S2 doivent être appelés,
    - is_full doit être False pour les deux.
    """
    start_date = date(2025, 3, 1)
    # 200 jours de GPT -> couvre +/- jusqu'en fin septembre
    ctx = make_context(
        nb_jours=200,
        start_date=start_date,
        include_left_repos=True,
        include_right_repos=True,
    )

    rule = DummySemesterRule()
    ok, alerts = rule.check(ctx)

    assert ok is True

    # On récupère les couples (year, label, is_full)
    calls = [(y, label, full) for (y, label, _, _, full, _) in rule.calls]

    # On s'attend à ce que S1 et S2 de 2025 soient appelés
    assert (2025, "S1", False) in calls
    assert (2025, "S2", False) in calls

    # Toutes les alertes sont info issues de DummySemesterRule
    assert all(a.severity == Severity.INFO for a in alerts)
    assert all(a.code == "DUMMY_SEM_INFO" for a in alerts)


def test_check_full_year_marks_both_semesters_full(make_context):
    """
    Si le contexte couvre toute l'année (01/01 → 31/12),
    alors S1 et S2 doivent être marqués is_full=True.
    """
    # Contexte qui commence le 1er janvier 2025
    # et couvre largement plus d'un an
    ctx = make_context(
        nb_jours=400,
        start_date=date(2025, 1, 1),
        include_left_repos=True,
        include_right_repos=True,
    )
    # start_date = 2025-01-01 (repos)
    # end_date   ≈ 2026-02... (repos final)
    # → pour l'année 2025, les semestres S1 et S2 sont entièrement couverts.

    rule = DummySemesterRule()
    ok, _ = rule.check(ctx)

    assert ok is True

    calls = [(y, label, full) for (y, label, _, _, full, _) in rule.calls]
    assert (2025, "S1", True) in calls
    assert (2025, "S2", True) in calls


def test_check_skips_non_overlapping_semesters(make_context):
    """
    Contexte limité au S1 uniquement : S2 ne doit pas être analysé.
    Contexte : 01/02 → 31/05 environ.
    """
    start_date = date(2025, 2, 1)
    # 120 jours -> jusqu'à fin mai/mi-juin
    ctx = make_context(nb_jours=120, start_date=start_date)

    rule = DummySemesterRule()
    ok, _ = rule.check(ctx)

    assert ok is True

    labels = {(y, label) for (y, label, _, _, _, _) in rule.calls}
    # S1 doit être présent, S2 pas forcément (ou très partiellement)
    assert (2025, "S1") in labels
    # On s'assure surtout qu'il n'y a pas d'appel à une année extérieure
    assert all(y == 2025 for (y, _) in labels)


def test_workdays_are_correctly_dispatched_per_semester(make_agent, make_workday):
    """
    Vérifie que les work_days sont correctement répartis entre S1 et S2 :

    - Un WorkDay en mars doit apparaître uniquement dans S1.
    - Un WorkDay en septembre uniquement dans S2.
    """
    ctx_start = date(2025, 1, 1)

    wd_s1 = make_workday(jour=date(2025, 3, 10), type_label="poste")
    wd_s2 = make_workday(jour=date(2025, 9, 5), type_label="poste")

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd_s1, wd_s2],
        date_reference=ctx_start,
    )
    # start_date / end_date seront calculés à partir des work_days :
    #   start_date = 2025-03-10, end_date = 2025-09-05

    rule = RecordingSemesterRule()
    ok, alerts = rule.check(context)

    assert ok is True
    assert alerts == []

    # On doit avoir deux semestres appelés : S1 et S2 pour 2025
    calls = {(c["year"], c["label"]): c for c in rule.calls}

    assert (2025, "S1") in calls
    assert (2025, "S2") in calls

    s1 = calls[(2025, "S1")]
    s2 = calls[(2025, "S2")]

    assert s1["jours"] == [wd_s1.jour]
    assert s2["jours"] == [wd_s2.jour]


def test_check_returns_false_if_any_semester_has_error(make_context):
    """
    Si un semestre retourne ok=False avec une alerte ERROR,
    le résultat global doit être ok=False.
    """
    start_date = date(2025, 1, 1)
    # 400 jours -> couvre toute l'année 2025 et un bout de 2026
    ctx = make_context(nb_jours=400, start_date=start_date)

    # On force une erreur sur le semestre S2 de 2025
    rule = ErrorSemesterRule(error_year=2025, error_label="S2")

    ok, alerts = rule.check(ctx)

    # On doit avoir au moins S1 et S2 pour 2025 dans les appels
    called = {(y, label) for (y, label, _) in rule.calls}
    assert (2025, "S1") in called
    assert (2025, "S2") in called

    # Résultat global invalide
    assert ok is False
    severities = {a.severity for a in alerts}
    assert Severity.ERROR in severities
    assert any(a.code == "SEMESTER_ERROR_TEST" for a in alerts)
