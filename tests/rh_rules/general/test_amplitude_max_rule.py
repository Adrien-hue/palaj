from core.rh_rules import AmplitudeMaxRule
from core.utils.domain_alert import Severity


def test_amplitude_within_limit(make_context_single_day, make_tranche):
    """Amplitude de 9h — conforme."""
    ctx = make_context_single_day()
    work_day = ctx.work_days[0]

    work_day.tranches = [
        make_tranche(heure_debut="08:00", heure_fin="17:00")
    ]

    ok, alerts = AmplitudeMaxRule().check_day(ctx, work_day)

    assert ok is True
    assert alerts == []


def test_amplitude_exceeds_limit(make_context_single_day, make_tranche):
    """Amplitude de 15h — non conforme."""
    ctx = make_context_single_day()
    work_day = ctx.work_days[0]

    work_day.tranches = [
        make_tranche(heure_debut="08:00", heure_fin="23:00")
    ]

    ok, alerts = AmplitudeMaxRule().check_day(ctx, work_day)

    assert ok is False
    # au moins une alerte ERROR
    assert any(a.severity == Severity.ERROR for a in alerts)
    # message qui parle bien d'amplitude
    assert any("Amplitude" in a.message for a in alerts)
