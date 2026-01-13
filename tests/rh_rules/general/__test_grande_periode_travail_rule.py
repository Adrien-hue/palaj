# tests/rh_rules/rules_period/test_grande_periode_travail_rule.py

import pytest

from core.rh_rules import GrandePeriodeTravailRule
from core.application.services.planning.grande_periode_travail_analyzer import (
    GrandePeriodeTravailAnalyzer,
)


# ---------------------------------------------------------------------
# 🧪 TESTS UNITAIRES DE BASE
# ---------------------------------------------------------------------


def test_gpt_trop_courte(make_context):
    """GPT < 3 jours → warning attendu, mais aucune erreur."""
    context = make_context(nb_jours=2)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)

    severities = [a.severity.name for a in alerts]

    # Le planning reste globalement valide, mais on signale les GPT courtes
    assert ok is True
    assert "ERROR" not in severities
    assert any(s == "WARNING" for s in severities)
    assert any("trop courte" in a.message.lower() for a in alerts)


def test_gpt_normale(make_context):
    """GPT 4 jours → conforme (aucune erreur ni avertissement)."""
    context = make_context(nb_jours=4)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)

    severities = [a.severity.name for a in alerts]
    assert ok is True
    assert "ERROR" not in severities
    assert "WARNING" not in severities


def test_gpt_trop_longue(make_context):
    """GPT > 6 jours → erreur attendue."""
    context = make_context(nb_jours=7)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)

    severities = [a.severity.name for a in alerts]
    assert ok is False
    assert any(s == "ERROR" for s in severities)
    assert any("trop longue" in a.message.lower() for a in alerts)


# ---------------------------------------------------------------------
# ⚙️ TESTS DE CAS MÉTIER MIXTES
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "pattern,expected_days",
    [
        (["POSTE", "ZCOT", "POSTE"], 3),
        (["POSTE", "ABSENCE", "POSTE"], 3),
        (["POSTE", "ABSENCE", "ZCOT", "POSTE"], 4),
    ],
)
def test_gpt_mixte(make_context, pattern, expected_days):
    """
    Les jours ZCOT et ABSENCE intégrés ne cassent pas la GPT.
    On vérifie côté analyzer directement.
    """
    context = make_context(pattern=pattern)
    service = GrandePeriodeTravailAnalyzer()

    gpts = service.detect(context)

    assert len(gpts) == 1
    gpt = gpts[0]

    assert gpt.nb_jours == expected_days
    assert gpt.has_zcot == ("ZCOT" in pattern)
    assert gpt.has_poste is True


# ---------------------------------------------------------------------
# 🚧 TESTS DE GPT TRONQUÉES
# ---------------------------------------------------------------------


def test_gpt_tronquee_gauche(make_context):
    """GPT tronquée à gauche → elle n'est pas comptée comme 'trop courte'."""
    context = make_context(nb_jours=2, include_left_repos=False)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)

    assert ok is True
    assert len(alerts) == 1
    # On s'attend à un résumé avec "0 trop courtes"
    assert "0 trop courtes" in alerts[0].message.lower()


def test_gpt_tronquee_droite(make_context):
    """GPT tronquée à droite → elle n'est pas comptée comme 'trop courte'."""
    context = make_context(nb_jours=2, include_right_repos=False)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)

    assert ok is True
    assert len(alerts) == 1
    assert "0 trop courtes" in alerts[0].message.lower()


# ---------------------------------------------------------------------
# 🔍 TESTS INFORMATIFS
# ---------------------------------------------------------------------


def test_gpt_de_6_jours_declenche_info(make_context):
    """GPT de 6 jours → info 'repos double obligatoire' dans le résumé."""
    context = make_context(nb_jours=6)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)

    assert ok is True
    info_msgs = [a.message.lower() for a in alerts if a.severity.name == "INFO"]
    assert any("repos double" in msg for msg in info_msgs)
