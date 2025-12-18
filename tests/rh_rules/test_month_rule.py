from datetime import date

import pytest

from core.rh_rules.month_rule import MonthRule
from core.utils.domain_alert import Severity
from core.domain.contexts.planning_context import PlanningContext


# ---------------------------------------------------------------------
# Implémentations de test
# ---------------------------------------------------------------------


class DummyMonthRule(MonthRule):
    """
    Règle mensuelle de test :
    - enregistre tous les appels à check_month
    - renvoie une alerte INFO pour chaque mois
    """

    name = "DummyMonthRule"

    def __init__(self):
        super().__init__()
        # (year, month, is_full)
        self.calls: list[tuple[int, int, bool]] = []

    def check_month(
        self,
        context,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        work_days,
    ):
        self.calls.append((year, month, is_full))
        alert = self.info(
            msg=f"Month {year}-{month:02d}, full={is_full}",
            code="DUMMY_MONTH_INFO",
        )
        return True, [alert]


class ErrorMonthRule(MonthRule):
    """
    Règle de test qui produit une erreur sur un mois précis
    pour vérifier la propagation de l'état global.
    """

    def __init__(self, error_year: int, error_month: int):
        super().__init__()
        self.error_year = error_year
        self.error_month = error_month
        self.calls: list[tuple[int, int, bool]] = []

    def check_month(
        self,
        context,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        work_days,
    ):
        self.calls.append((year, month, is_full))
        if (year, month) == (self.error_year, self.error_month):
            alert = self.error(
                msg=f"Erreur sur {year}-{month:02d}",
                code="MONTH_ERROR_TEST",
            )
            return False, [alert]
        else:
            return True, [self.info(f"OK {year}-{month:02d}")]


class RecordingMonthRule(MonthRule):
    """
    Règle de test pour vérifier le dispatch des WorkDay par mois.
    """

    def __init__(self):
        super().__init__()
        self.calls: list[dict] = []

    def check_month(
        self,
        context,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        work_days,
    ):
        self.calls.append(
            {
                "year": year,
                "month": month,
                "is_full": is_full,
                "jours": sorted([wd.jour for wd in work_days]),
            }
        )
        return True, []


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_month_rule_is_abstract():
    """MonthRule ne doit pas être instanciable directement."""
    with pytest.raises(TypeError):
        MonthRule()  # type: ignore[abstract]


def test_iter_months_in_context_same_year():
    """_iter_months_in_context doit générer tous les mois entre start et end, même année."""
    rule = DummyMonthRule()

    start = date(2025, 1, 15)
    end = date(2025, 4, 3)

    months = list(rule._iter_months_in_context(start, end))

    assert months == [
        (2025, 1),
        (2025, 2),
        (2025, 3),
        (2025, 4),
    ]


def test_iter_months_in_context_across_years():
    """_iter_months_in_context doit gérer le passage à l'année suivante."""
    rule = DummyMonthRule()

    start = date(2025, 11, 10)
    end = date(2026, 2, 5)

    months = list(rule._iter_months_in_context(start, end))

    assert months == [
        (2025, 11),
        (2025, 12),
        (2026, 1),
        (2026, 2),
    ]


def test_check_with_missing_dates_returns_error():
    """
    Si start_date ou end_date manquent, check() doit renvoyer une erreur MONTH_NO_DATES.

    On utilise un mini contexte factice avec start_date / end_date = None,
    plutôt qu'un PlanningContext réel (dont les dates sont calculées à partir
    de work_days et non assignables).
    """

    class ContextNoDates:
        start_date = None
        end_date = None

    ctx = ContextNoDates()
    rule = DummyMonthRule()

    ok, alerts = rule.check(ctx)  # pyright: ignore[reportArgumentType]

    assert ok is False
    assert len(alerts) == 1
    a = alerts[0]
    assert a.severity == Severity.ERROR
    assert a.code == "MONTH_NO_DATES"
    assert "Impossible de déterminer les bornes" in a.message


def test_check_with_no_workdays_returns_true_and_no_alerts():
    """
    Si le contexte a des bornes mais aucun work_day, check() doit retourner (True, [])
    grâce au early-return sur context.work_days.
    """

    class EmptyContext:
        start_date = date(2025, 1, 1)
        end_date = date(2025, 3, 31)
        work_days = []

    ctx = EmptyContext()
    rule = DummyMonthRule()

    ok, alerts = rule.check(ctx)  # pyright: ignore[reportArgumentType]

    assert ok is True
    assert alerts == []


def test_check_calls_check_month_for_each_month_and_sets_is_full(make_context):
    """
    Contexte réel sur 2 mois :
      - start_date ≈ 2025-01-01
      - GPT qui déborde largement sur février

    On vérifie que :
      - janvier est vu comme 'full'
      - février comme 'partial'
    selon start/end du PlanningContext.
    """
    start_date = date(2025, 1, 1)
    # 40 jours de POSTE après start_date => ça va au moins jusqu'à début février
    ctx = make_context(
        nb_jours=40,
        start_date=start_date,
        include_left_repos=True,
        include_right_repos=True,
    )

    rule = DummyMonthRule()
    ok, alerts = rule.check(ctx)

    assert ok is True

    # On s'attend à ce que le contexte couvre janvier complet,
    # mais pas tout février.
    assert len(rule.calls) >= 2
    jan_call = rule.calls[0]
    feb_call = rule.calls[1]

    assert jan_call[0] == 2025 and jan_call[1] == 1
    assert jan_call[2] is True   # janvier complet
    assert feb_call[0] == 2025 and feb_call[1] == 2
    assert feb_call[2] is False  # février partiel

    # Chaque mois donne au moins une alerte INFO
    assert all(a.severity == Severity.INFO for a in alerts)


def test_check_returns_false_if_any_month_has_error(make_context):
    """
    Si une alerte ERROR est produite sur un mois,
    le résultat global doit être ok=False.
    On construit un contexte réel qui couvre au moins jan/fév/mars.
    """
    start_date = date(2025, 1, 1)
    # 70 jours de POSTE => ça couvre environ jusqu'à mi-mars
    ctx = make_context(
        nb_jours=70,
        start_date=start_date,
        include_left_repos=True,
        include_right_repos=True,
    )

    # On force une erreur sur février 2025
    rule = ErrorMonthRule(error_year=2025, error_month=2)

    ok, alerts = rule.check(ctx)

    called_months = [(y, m) for (y, m, _) in rule.calls]
    assert (2025, 1) in called_months
    assert (2025, 2) in called_months
    assert (2025, 3) in called_months

    assert ok is False
    severities = {a.severity for a in alerts}
    assert Severity.ERROR in severities
    assert any(a.code == "MONTH_ERROR_TEST" for a in alerts)


def test_month_rule_works_with_real_planning_context(make_context):
    """
    Petit test d'intégration : validation qu'une MonthRule
    fonctionne correctement sur un vrai PlanningContext
    construit avec make_context.
    """
    ctx = make_context(nb_jours=5, start_date=date(2025, 4, 1))

    rule = DummyMonthRule()
    ok, alerts = rule.check(ctx)

    assert ok is True
    assert len(rule.calls) >= 1
    assert len(alerts) == len(rule.calls)
    assert all(a.code == "DUMMY_MONTH_INFO" for a in alerts)


def test_month_rule_dispatches_workdays_per_month(make_agent, make_workday):
    """
    Vérifie que les work_days sont correctement dispatchés par mois
    dans les arguments de check_month.
    """
    agent = make_agent()

    wd_jan = make_workday(jour=date(2025, 1, 10), type_label="poste")
    wd_feb = make_workday(jour=date(2025, 2, 5), type_label="poste")
    wd_mar = make_workday(jour=date(2025, 3, 20), type_label="poste")

    ctx = PlanningContext(
        agent=agent,
        work_days=[wd_jan, wd_feb, wd_mar],
        date_reference=wd_jan.jour,
    )

    rule = RecordingMonthRule()
    ok, alerts = rule.check(ctx)

    assert ok is True
    assert alerts == []

    calls = {(c["year"], c["month"]): c for c in rule.calls}

    assert (2025, 1) in calls
    assert (2025, 2) in calls
    assert (2025, 3) in calls

    assert calls[(2025, 1)]["jours"] == [wd_jan.jour]
    assert calls[(2025, 2)]["jours"] == [wd_feb.jour]
    assert calls[(2025, 3)]["jours"] == [wd_mar.jour]
