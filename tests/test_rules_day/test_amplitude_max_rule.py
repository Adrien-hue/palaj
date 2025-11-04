from datetime import time
from core.rh_rules.rule_amplitude_max import AmplitudeMaxRule
from core.utils.domain_alert import Severity


def test_amplitude_within_limit(base_context, make_tranche):
    """Amplitude de 9h — conforme."""
    t = make_tranche(debut=(8, 0), fin=(17, 0))
    base_context.work_days[0].tranches = [t]

    rule = AmplitudeMaxRule()
    ok, alerts = rule.check(base_context)

    assert ok is True
    assert alerts == []


def test_amplitude_exceeds_limit(base_context, make_tranche):
    """Amplitude de 17h — non conforme."""
    t = make_tranche(debut=(6, 0), fin=(23, 0))
    base_context.work_days[0].tranches = [t]

    rule = AmplitudeMaxRule()
    ok, alerts = rule.check(base_context)

    assert ok is False
    assert any(a.severity == Severity.ERROR for a in alerts)
    assert any("Amplitude" in a.message for a in alerts)
