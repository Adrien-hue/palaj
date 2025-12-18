from datetime import date

from core.rh_rules import DureeTravailRule
from core.utils.domain_alert import Severity


def _get_single_workday(ctx):
    assert len(ctx.work_days) == 1
    return ctx.work_days[0]


def test_duree_travail_minimum(make_context_single_day):
    """
    Durée inférieure au minimum — alerte attendue.
    08:00 → 12:00 = 4h de travail (< 5h30).
    """
    ctx = make_context_single_day(
        jour=date(2025, 1, 1),
        type_label="poste",
        h1="08:00",
        h2="12:00",
    )
    wd = _get_single_workday(ctx)

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is False
    assert any("insuffisante" in a.message for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)
    assert any(a.code == "DUREE_TRAVAIL_MIN_INSUFFISANTE" for a in alerts)


def test_duree_travail_maximum(make_context_single_day):
    """
    Durée supérieure à la limite jour — alerte attendue.
    08:00 → 20:30 = 12h30 (> 10h).
    """
    ctx = make_context_single_day(
        jour=date(2025, 1, 2),
        type_label="poste",
        h1="08:00",
        h2="20:30",
    )
    wd = _get_single_workday(ctx)

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is False
    assert any("excessive" in a.message for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)
    assert any(a.code == "DUREE_TRAVAIL_MAX_DEPASSEE" for a in alerts)


def test_duree_travail_normale(make_context_single_day):
    """
    Durée normale — conforme.
    07:00 → 15:00 = 8h.
    """
    ctx = make_context_single_day(
        jour=date(2025, 1, 3),
        type_label="poste",
        h1="07:00",
        h2="15:00",
    )
    wd = _get_single_workday(ctx)

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is True
    assert alerts == []


# ----------------------------------------------------------------------
# Tests supplémentaires : seuils et cas particuliers
# ----------------------------------------------------------------------


def test_duree_travail_exactement_au_minimum(make_context_single_day):
    """
    Durée exactement au minimum (5h30) — conforme.
    08:00 → 13:30 = 5h30.
    """
    ctx = make_context_single_day(
        jour=date(2025, 1, 4),
        type_label="poste",
        h1="08:00",
        h2="13:30",
    )
    wd = _get_single_workday(ctx)

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is True
    assert alerts == []


def test_duree_travail_exactement_au_maximum_jour(make_context_single_day):
    """
    Durée exactement à la limite jour (10h) — conforme.
    08:00 → 18:00 = 10h.
    """
    ctx = make_context_single_day(
        jour=date(2025, 1, 5),
        type_label="poste",
        h1="08:00",
        h2="18:00",
    )
    wd = _get_single_workday(ctx)

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is True
    assert alerts == []


def test_duree_travail_nuit_depasse_maximum(
    make_context_single_day, make_tranche
):
    """
    Service de nuit avec durée > 8h30 — alerte nuit attendue.
    22:00 → 07:00 = 9h (si implémentation span nuit).
    """
    # On crée un contexte simple puis on remplace les tranches
    ctx = make_context_single_day(
        jour=date(2025, 1, 6),
        type_label="poste",
    )
    wd = _get_single_workday(ctx)
    wd.tranches = [
        make_tranche(heure_debut="22:00", heure_fin="07:00")
    ]

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is False
    assert any("excessive" in a.message for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)
    # Pour un service de nuit, on attend le code spécifique
    assert any(a.code == "DUREE_TRAVAIL_MAX_NUIT_DEPASSEE" for a in alerts)


def test_duree_travail_nuit_exactement_au_maximum(
    make_context_single_day, make_tranche
):
    """
    Service de nuit exactement à 8h30 — conforme.
    22:00 → 06:30 = 8h30.
    """
    ctx = make_context_single_day(
        jour=date(2025, 1, 7),
        type_label="poste",
    )
    wd = _get_single_workday(ctx)
    wd.tranches = [
        make_tranche(heure_debut="22:00", heure_fin="06:30")
    ]

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is True
    assert alerts == []


def test_jour_non_travaille_aucune_alerte(make_context_single_day):
    """
    Jour non travaillé (repos, par exemple) — aucune vérification.
    """
    ctx = make_context_single_day(
        jour=date(2025, 1, 8),
        type_label="repos",  # doit conduire à is_working() == False
    )
    wd = _get_single_workday(ctx)

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is True
    assert alerts == []


def test_plusieurs_alertes_si_tres_court_et_nuit_longue(
    make_context_single_day, make_tranche
):
    """
    Cas extrême : si l'implémentation permet plusieurs tranches, on
    peut théoriquement provoquer min ET max, mais ici on valide juste
    que plusieurs alertes sont possibles.
    """
    ctx = make_context_single_day(
        jour=date(2025, 1, 9),
        type_label="poste",
    )
    wd = _get_single_workday(ctx)

    # On force une very long nuit pour dépasser largement le max nuit.
    wd.tranches = [
        make_tranche(heure_debut="21:00", heure_fin="08:00"),
    ]

    rule = DureeTravailRule()
    ok, alerts = rule.check_day(ctx, wd)

    assert ok is False
    assert len(alerts) >= 1
    assert any(a.severity == Severity.ERROR for a in alerts)
    # On vérifie au moins qu'on a une alerte "excessive"
    assert any("excessive" in a.message for a in alerts)
