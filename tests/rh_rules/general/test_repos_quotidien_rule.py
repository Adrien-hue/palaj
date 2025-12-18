from datetime import date

from core.rh_rules import ReposQuotidienRule
from core.utils.domain_alert import Severity
from core.domain.contexts.planning_context import PlanningContext


def test_repos_insuffisant(make_agent, make_workday):
    """
    Travail de nuit → matin sans repos suffisant.
    Veille : 22:00–06:20
    Jour :   06:20–14:00
    → repos quotidien < minimum, on attend une erreur.
    """
    jour_veille = date(2025, 1, 18)
    jour_jour = date(2025, 1, 19)

    # Service de nuit la veille
    wd_veille = make_workday(
        jour=jour_veille,
        type_label="poste",
        nocturne=True,
        h1="22:00",
        h2="06:20",
    )

    # Service du matin le lendemain (repos quasi nul)
    wd_jour = make_workday(
        jour=jour_jour,
        type_label="poste",
        h1="06:20",
        h2="14:00",
    )

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd_veille, wd_jour],
        date_reference=jour_jour,
    )

    rule = ReposQuotidienRule()
    ok, alerts = rule.check_day(context, wd_jour)

    assert ok is False
    assert any("Repos quotidien insuffisant" in a.message for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)
    assert any(a.code == "REPOS_QUOTIDIEN_INSUFFISANT" for a in alerts)


def test_repos_suffisant_standard_jour(make_agent, make_workday):
    """
    Deux journées de jour avec repos standard largement suffisant.
    Veille : 08:00–16:00
    Jour :   08:40–16:40 le lendemain
    → repos ≈ 16h40 (> 12h20) → OK.
    """
    jour_veille = date(2025, 1, 10)
    jour_jour = date(2025, 1, 11)

    wd_veille = make_workday(
        jour=jour_veille,
        type_label="poste",
        h1="08:00",
        h2="16:00",
    )
    wd_jour = make_workday(
        jour=jour_jour,
        type_label="poste",
        h1="08:40",
        h2="16:40",
    )

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd_veille, wd_jour],
        date_reference=jour_jour,
    )

    rule = ReposQuotidienRule()
    ok, alerts = rule.check_day(context, wd_jour)

    assert ok is True
    assert alerts == []


def test_repos_suffisant_apres_travail_de_nuit(make_agent, make_workday):
    """
    Travail de nuit la veille, repos de 14h pile → OK.
    Veille : 22:00–06:00
    Jour :   20:00–23:00 le même jour (J+1)
    Repos = 14h → respecte le minimum nuit (14h).
    """
    jour_veille = date(2025, 1, 12)
    jour_jour = date(2025, 1, 13)

    wd_veille = make_workday(
        jour=jour_veille,
        type_label="poste",
        nocturne=True,
        h1="22:00",
        h2="06:00",
    )
    wd_jour = make_workday(
        jour=jour_jour,
        type_label="poste",
        h1="20:00",
        h2="23:00",
    )

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd_veille, wd_jour],
        date_reference=jour_jour,
    )

    rule = ReposQuotidienRule()
    ok, alerts = rule.check_day(context, wd_jour)

    assert ok is True
    assert alerts == []


def test_premier_jour_travaille_sans_precedent(make_agent, make_workday):
    """
    S'il n'y a pas de jour travaillé précédent, la règle ne doit pas déclencher d'alerte.
    """
    jour = date(2025, 1, 15)

    wd = make_workday(
        jour=jour,
        type_label="poste",
        h1="08:00",
        h2="16:00",
    )

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd],
        date_reference=jour,
    )

    rule = ReposQuotidienRule()
    ok, alerts = rule.check_day(context, wd)

    assert ok is True
    assert alerts == []


def test_jour_de_repos_ou_non_travaille_ignored(make_agent, make_workday):
    """
    Jour de repos : la règle doit s'ignorer (pas de contrôle).
    """
    jour = date(2025, 1, 16)

    wd = make_workday(
        jour=jour,
        type_label="repos",
    )

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd],
        date_reference=jour,
    )

    rule = ReposQuotidienRule()
    ok, alerts = rule.check_day(context, wd)

    assert ok is True
    assert alerts == []


def test_repos_insuffisant_standard_jour(make_agent, make_workday):
    """
    Deux journées de jour avec repos < 12h20 → alerte standard.
    Veille : 08:00–18:00
    Jour :   05:00–13:00 le lendemain
    Repos ≈ 11h → insuffisant.
    """
    jour_veille = date(2025, 1, 20)
    jour_jour = date(2025, 1, 21)

    wd_veille = make_workday(
        jour=jour_veille,
        type_label="poste",
        h1="08:00",
        h2="18:00",
    )
    wd_jour = make_workday(
        jour=jour_jour,
        type_label="poste",
        h1="05:00",
        h2="13:00",
    )

    context = PlanningContext(
        agent=make_agent(),
        work_days=[wd_veille, wd_jour],
        date_reference=jour_jour,
    )

    rule = ReposQuotidienRule()
    ok, alerts = rule.check_day(context, wd_jour)

    assert ok is False
    assert any("Repos quotidien insuffisant" in a.message for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)
    assert any(a.code == "REPOS_QUOTIDIEN_INSUFFISANT" for a in alerts)
