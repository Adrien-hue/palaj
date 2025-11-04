from datetime import date, time, timedelta
from core.rh_rules.rule_repos_quotidien import ReposQuotidienRule
from core.utils.domain_alert import Severity
from core.domain.entities.work_day import WorkDay
from core.domain.entities import EtatJourAgent, TypeJour


def test_repos_insuffisant(sample_agent, make_tranche):
    """Travail de nuit → matin sans repos suffisant."""
    t_nuit = make_tranche(abbr="NJ", debut=(22, 0), fin=(6, 20))
    t_matin = make_tranche(abbr="MJ", debut=(6, 20), fin=(14, 0))

    jour_veille = date(2025, 1, 18)
    jour_jour = date(2025, 1, 19)

    wd_veille = WorkDay(
        jour=jour_veille,
        etat=EtatJourAgent(sample_agent.id, jour_veille, TypeJour.POSTE),
        tranches=[t_nuit],
    )
    wd_jour = WorkDay(
        jour=jour_jour,
        etat=EtatJourAgent(sample_agent.id, jour_jour, TypeJour.POSTE),
        tranches=[t_matin],
    )

    from core.domain.contexts.planning_context import PlanningContext
    context = PlanningContext(
        agent=sample_agent,
        work_days=[wd_veille, wd_jour],
        date_reference=jour_jour,
    )

    rule = ReposQuotidienRule()
    ok, alerts = rule.check(context)

    assert ok is False
    assert any("Repos quotidien insuffisant" in a.message for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)
