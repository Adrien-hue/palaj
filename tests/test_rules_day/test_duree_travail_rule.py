from core.rh_rules.rule_duree_travail import DureeTravailRule
from core.utils.domain_alert import Severity


def test_duree_travail_minimum(base_context, make_tranche):
    """Durée inférieure au minimum — alerte attendue."""
    t = make_tranche(debut=(8, 0), fin=(12, 0))  # 4h
    base_context.work_days[0].tranches = [t]

    rule = DureeTravailRule()
    ok, alerts = rule.check(base_context)

    assert ok is False
    assert any("insuffisante" in a.message for a in alerts)


def test_duree_travail_maximum(base_context, make_tranche):
    """Durée supérieure à la limite — alerte attendue."""
    t = make_tranche(debut=(8, 0), fin=(20, 30))  # 12h30
    base_context.work_days[0].tranches = [t]

    rule = DureeTravailRule()
    ok, alerts = rule.check(base_context)

    assert ok is False
    assert any("excessive" in a.message for a in alerts)


def test_duree_travail_normale(base_context, make_tranche):
    """Durée normale — conforme."""
    t = make_tranche(debut=(7, 0), fin=(15, 0))
    base_context.work_days[0].tranches = [t]

    rule = DureeTravailRule()
    ok, alerts = rule.check(base_context)

    assert ok is True
    assert alerts == []
