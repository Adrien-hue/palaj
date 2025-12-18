# tests/rh_rules/rules_period/test_conges_annuels.py

from datetime import date, timedelta

import pytest

from core.rh_rules import CongesAnnuelRule
from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour
from core.utils.domain_alert import Severity

# -------------------------
# Période partielle (pas l'année complète)
# -------------------------


def test_partial_period_with_some_conges_only_info(make_agent, make_workday):
    """
    Période qui ne couvre pas l'année complète :
    - la règle ne doit pas générer d'ERROR
    - mais un résumé INFO avec le total de congés.
    """
    rule = CongesAnnuelRule()

    d0 = date(2024, 3, 1)
    agent = make_agent()

    wds = [
        make_workday(jour=d0 + timedelta(days=0), type_label="poste", agent=agent),
        make_workday(jour=d0 + timedelta(days=1), type_label="conge", agent=agent),
        make_workday(jour=d0 + timedelta(days=2), type_label="repos", agent=agent),
        make_workday(jour=d0 + timedelta(days=3), type_label="conge", agent=agent),
    ]
    ctx = PlanningContext(agent=agent, work_days=wds)

    ok, alerts = rule.check(ctx)

    assert ok is True
    errors = [a for a in alerts if a.is_error()]
    infos = [a for a in alerts if a.is_info()]
    assert len(errors) == 0
    assert len(infos) >= 1
    assert any("congés annuels" in a.message.lower() for a in infos)


def test_partial_period_no_conges_only_info(make_agent, make_workday):
    """
    Période partielle sans aucun congé :
    - aucune ERROR
    - une INFO expliquant qu'il n'y a pas de congés sur la période.
    """
    rule = CongesAnnuelRule()

    d0 = date(2024, 4, 1)
    agent = make_agent()

    wds = [
        make_workday(jour=d0 + timedelta(days=i), type_label="poste", agent=agent)
        for i in range(5)
    ]
    ctx = PlanningContext(agent=agent, work_days=wds)

    ok, alerts = rule.check(ctx)
    
    assert ok is True
    errors = [a for a in alerts if a.is_error()]
    infos = [a for a in alerts if a.is_info()]
    assert len(errors) == 0
    assert len(infos) == 1
    assert "CONGES_ANNUELS_SYNTHESIS" == infos[0].code

# -------------------------
# Année complète : cas OK
# -------------------------


def test_full_year_ok_enough_days_and_one_long_block(make_year_context_conges):
    """
    Année complète :
    - total congés >= 28
    - au moins une période de 15 jours consécutifs de congés
    => aucune ERROR.
    """
    rule = CongesAnnuelRule()

    # Bloc de 15 jours consécutifs en mars
    start_block = date(2024, 3, 1)
    block_15 = [start_block + timedelta(days=i) for i in range(15)]

    # + quelques jours isolés pour dépasser 28 au total
    extra = [date(2024, 5, 1), date(2024, 6, 1), date(2024, 7, 1), date(2024, 8, 1)]
    conges = block_15 + extra  # 19 jours

    # On veut >= 28, donc on complète
    while len(conges) < 28:
        conges.append(date(2024, 9, 1) + timedelta(days=len(conges)))

    ctx = make_year_context_conges(year=2024, conge_days=conges)

    ok, alerts = rule.check(ctx)

    assert ok is True
    errors = [a for a in alerts if a.is_error()]
    assert len(errors) == 0

    infos = [a for a in alerts if a.is_info()]
    assert any("congés annuels" in a.message.lower() for a in infos)


# -------------------------
# Année complète : pas assez de jours
# -------------------------


def test_full_year_not_enough_total_conges(make_year_context_conges):
    """
    Année complète, mais total de congés < 28 => ERROR.
    """
    rule = CongesAnnuelRule()

    # Bloc de 10 jours consécutifs seulement
    start_block = date(2024, 3, 1)
    block_10 = [start_block + timedelta(days=i) for i in range(10)]

    ctx = make_year_context_conges(year=2024, conge_days=block_10)

    ok, alerts = rule.check(ctx)

    assert ok is False
    errors = [a for a in alerts if a.is_error()]
    assert len(errors) >= 1
    assert any("insuffisant" in a.message.lower() for a in errors)


# -------------------------
# Année complète : pas de bloc de 15 jours
# -------------------------


def test_full_year_enough_days_but_no_long_block(make_year_context_conges):
    """
    Total congés >= 28 mais aucune période de 15 jours consécutifs :
    => ERROR spécifique sur le bloc long manquant.
    """
    rule = CongesAnnuelRule()

    # 30 jours de congés, mais jamais plus de 6 d'affilée
    conges: list[date] = []
    start = date(2024, 2, 1)

    for k in range(5):
        base = start + timedelta(days=10 * k)
        for i in range(6):
            conges.append(base + timedelta(days=i))

    assert len(conges) == 30  # sécurité

    ctx = make_year_context_conges(year=2024, conge_days=conges)

    ok, alerts = rule.check(ctx)

    assert ok is False
    errors = [a for a in alerts if a.is_error()]
    assert len(errors) >= 1
    assert any("15" in a.message for a in errors)


# -------------------------
# Année complète : aucun congé
# -------------------------


def test_full_year_no_conges_error(make_year_context_conges):
    """
    Année complète sans aucun congé :
    => ERROR explicite.
    """
    rule = CongesAnnuelRule()

    ctx = make_year_context_conges(year=2024, conge_days=[])

    ok, alerts = rule.check(ctx)

    assert ok is False
    errors = [a for a in alerts if a.is_error()]
    # on attend 2 erreurs : total insuffisant + aucune période consécutive
    assert len(errors) == 2
    assert "annuels insuffisant" in errors[0].message.lower()
    assert "aucune période de congés consécutifs" in errors[1].message.lower()
