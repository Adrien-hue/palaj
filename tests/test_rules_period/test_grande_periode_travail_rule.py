import pytest

from core.rh_rules.rule_grande_periode_travail import GrandePeriodeTravailRule
from core.domain.services.grande_periode_travail_service import GrandePeriodeTravailService


# ---------------------------------------------------------------------
# 🧪 TESTS UNITAIRES DE BASE
# ---------------------------------------------------------------------

def test_gpt_trop_courte(make_context_with_gpt):
    """GPT < 3 jours → warning attendu, mais aucune erreur."""
    context = make_context_with_gpt(nb_jours=2)
    rule = GrandePeriodeTravailRule()
    ok, alerts = rule.check(context)

    severities = [a.severity.name for a in alerts]
    assert ok is True  # le planning reste globalement valide
    assert "ERROR" not in severities
    assert any("WARNING" == s for s in severities)
    assert any("trop courte" in a.message.lower() for a in alerts)


def test_gpt_normale(make_context_with_gpt):
    """GPT 4 jours → conforme (aucune erreur ni avertissement)."""
    context = make_context_with_gpt(nb_jours=4)
    rule = GrandePeriodeTravailRule()
    ok, alerts = rule.check(context)

    severities = [a.severity.name for a in alerts]
    assert ok is True
    assert "ERROR" not in severities
    assert "WARNING" not in severities


def test_gpt_trop_longue(make_context_with_gpt):
    """GPT > 6 jours → erreur attendue."""
    context = make_context_with_gpt(nb_jours=7)
    rule = GrandePeriodeTravailRule()
    ok, alerts = rule.check(context)

    severities = [a.severity.name for a in alerts]
    assert ok is False
    assert any("ERROR" == s for s in severities)
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
def test_gpt_mixte(make_context_with_gpt, pattern, expected_days):
    """Les jours ZCOT et ABSENCE intégrés ne cassent pas la GPT."""
    context = make_context_with_gpt(pattern=pattern)
    service = GrandePeriodeTravailService()
    gpts = service.detect_gpts(context)

    assert len(gpts) == 1
    gpt = gpts[0]
    assert gpt.nb_jours == expected_days
    assert gpt.has_zcot == ("ZCOT" in pattern)
    assert gpt.has_poste is True


# ---------------------------------------------------------------------
# 🚧 TESTS DE GPT TRONQUÉES
# ---------------------------------------------------------------------

def test_gpt_tronquee_gauche(make_context_with_gpt):
    """GPT tronquée à gauche → pas de 'trop courte'."""
    context = make_context_with_gpt(nb_jours=2, include_left_repos=False)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)
    assert all("trop courte" not in a.message.lower() for a in alerts)


def test_gpt_tronquee_droite(make_context_with_gpt):
    """GPT tronquée à droite → pas de 'trop courte'."""
    context = make_context_with_gpt(nb_jours=2, include_right_repos=False)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)
    assert all("trop courte" not in a.message.lower() for a in alerts)


# ---------------------------------------------------------------------
# 🔍 TESTS INFORMATIFS
# ---------------------------------------------------------------------

def test_gpt_de_6_jours_declenche_info(make_context_with_gpt):
    """GPT de 6 jours → info 'repos double obligatoire'."""
    context = make_context_with_gpt(nb_jours=6)
    rule = GrandePeriodeTravailRule()

    ok, alerts = rule.check(context)
    info_msgs = [a.message for a in alerts if a.severity.name == "INFO"]

    assert ok is True
    assert any("repos double" in msg.lower() for msg in info_msgs)