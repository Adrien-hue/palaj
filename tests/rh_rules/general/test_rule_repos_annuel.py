# tests/rh_rules/rules_period/test_rule_repos_annuel.py

from datetime import date, timedelta

from core.rh_rules import ReposAnnuelRule
from core.utils.domain_alert import Severity


def test_no_repos_detected(make_repos_context):
    rule = ReposAnnuelRule()
    ctx = ctx = make_repos_context(dates_repos=[], year=2025, full_year=True)

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert len(alerts) == 1
    assert alerts[0].severity == Severity.INFO
    assert "Aucune période de repos" in alerts[0].message


def test_partial_year_only_info(make_repos_context):
    rule = ReposAnnuelRule()

    # 5–10 janvier = pas une année complète
    dates = [date(2024, 1, d) for d in range(5, 11)]
    ctx = make_repos_context(dates)

    ok, alerts = rule.check(ctx)

    assert ok is True
    # 1 INFO résumé + pas d’erreurs (période non full-year)
    assert len(alerts) == 1
    assert alerts[0].severity == Severity.INFO


def test_full_year_all_good(make_repos_context):
    """
    Année complète :
    - au moins 52 repos doubles
    - dont au moins 14 WERP (et donc 12 RPSD inclus)
    → aucune erreur
    """
    rule = ReposAnnuelRule()

    dates: list[date] = []

    # 14 WERP (samedi-dimanche) donc >= 12 RPSD
    start_samedi = date(2024, 1, 6)  # un samedi
    for i in range(14):
        d = start_samedi + timedelta(weeks=i)
        dates += [d, d + timedelta(days=1)]

    # Compléter pour atteindre 52 RP doubles (en évitant les chevauchements)
    while len(dates) // 2 < 52:
        last = max(dates)
        base = last + timedelta(days=3)
        dates += [base, base + timedelta(days=1)]

    ctx = make_repos_context(dates_repos=dates, full_year=True, year=2024)

    ok, alerts = rule.check(ctx)

    errors = [a for a in alerts if a.severity == Severity.ERROR]
    assert len(errors) == 0


def test_full_year_not_enough_rp_double(make_repos_context):
    """
    Année complète mais seulement 10 repos doubles → erreur sur RP doubles.
    """
    rule = ReposAnnuelRule()

    dates: list[date] = []
    base = date(2024, 1, 6)
    for i in range(10):
        d = base + timedelta(weeks=i)
        dates += [d, d + timedelta(days=1)]

    ctx = make_repos_context(dates_repos=dates, full_year=True, year=2024)

    ok, alerts = rule.check(ctx)

    errors = [a for a in alerts if a.severity == Severity.ERROR]
    assert any("Repos doubles insuffisants" in e.message for e in errors)


def test_full_year_not_enough_werp(make_repos_context):
    """
    52 repos doubles mais aucun week-end WERP (sam-dim / dim-lun) → erreur WERP.
    """
    rule = ReposAnnuelRule()

    dates: list[date] = []
    start = date(2024, 1, 2)  # un mardi par ex. → pas WERP
    for i in range(52):
        d = start + timedelta(weeks=i)
        dates += [d, d + timedelta(days=1)]

    ctx = make_repos_context(dates_repos=dates, full_year=True, year=2024)

    ok, alerts = rule.check(ctx)

    errors = [a for a in alerts if a.severity == Severity.ERROR]
    assert any("WERP insuffisants" in e.message for e in errors)


def test_full_year_not_enough_rpsd(make_repos_context):
    """
    52 repos doubles, mais aucun samedi-dimanche → erreur RPSD.
    """
    rule = ReposAnnuelRule()

    dates: list[date] = []
    start = date(2024, 1, 1)  # lundi
    for i in range(52):
        d = start + timedelta(days=2 * i)
        dates += [d, d + timedelta(days=1)]

    ctx = make_repos_context(dates_repos=dates, full_year=True, year=2024)

    ok, alerts = rule.check(ctx)

    errors = [a for a in alerts if a.severity == Severity.ERROR]
    assert any("RPSD insuffisants" in e.message for e in errors)