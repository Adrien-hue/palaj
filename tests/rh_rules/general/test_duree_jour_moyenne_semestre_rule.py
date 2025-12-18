# tests/rh_rules/rules_period/test_duree_jour_moyenne_semestre.py

from datetime import date, timedelta

from core.rh_rules import DureeJourMoyenneSemestreRule
from core.rh_rules.constants.regime_rules import (
    REGIME_AVG_SERVICE_MINUTES,
    REGIME_AVG_TOLERANCE_MINUTES,
)
from core.domain.contexts.planning_context import PlanningContext
from core.utils.domain_alert import Severity


def test_no_work_days_returns_ok_and_no_alerts(make_agent):
    """
    Aucun WorkDay : la règle doit considérer que tout est OK (rien à analyser).
    """
    rule = DureeJourMoyenneSemestreRule()
    ctx = PlanningContext(agent=make_agent(regime_id=0), work_days=[])

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert alerts == []


def test_regime_unknown_returns_info_only(make_semester_context):
    """
    Régime non configuré dans REGIME_AVG_SERVICE_MINUTES :
    → INFO 'non applicable', pas d'erreur.
    """
    rule = DureeJourMoyenneSemestreRule()

    # régime non configuré
    ctx = make_semester_context(
        year=2024,
        regime_id=999,
        sem="S1",
        minutes_per_day=480,
        full_semester=True,
    )

    ok, alerts = rule.check(ctx)

    assert ok is True
    assert len(alerts) == 1
    assert alerts[0].severity == Severity.INFO
    assert "non applicable" in alerts[0].message.lower()


def test_full_semester_conforme(make_semester_context):
    """
    Semestre complet, durée moyenne exactement égale à la cible :
    → INFO conforme, aucun ERROR.
    """
    rule = DureeJourMoyenneSemestreRule()

    regime_id = next(iter(REGIME_AVG_SERVICE_MINUTES.keys()))
    target = REGIME_AVG_SERVICE_MINUTES[regime_id]

    ctx = make_semester_context(
        year=2024,
        regime_id=regime_id,
        sem="S1",
        minutes_per_day=target,
        full_semester=True,
    )

    ok, alerts = rule.check(ctx)

    errors = [a for a in alerts if a.severity == Severity.ERROR]
    infos = [a for a in alerts if a.severity == Severity.INFO]

    assert ok is True
    assert len(errors) == 0
    assert any("conforme pour le semestre complet" in a.message.lower()
               for a in infos)


def test_full_semester_non_conforme(make_semester_context):
    """
    Semestre complet, moyenne hors tolérance :
    → ERROR.
    """
    rule = DureeJourMoyenneSemestreRule()

    regime_id = next(iter(REGIME_AVG_SERVICE_MINUTES.keys()))
    target = REGIME_AVG_SERVICE_MINUTES[regime_id]
    tol = REGIME_AVG_TOLERANCE_MINUTES

    # On force une moyenne au-delà de la tolérance
    minutes = target + tol + 30

    ctx = make_semester_context(
        year=2024,
        regime_id=regime_id,
        sem="S1",
        minutes_per_day=minutes,
        full_semester=True,
    )

    ok, alerts = rule.check(ctx)

    errors = [a for a in alerts if a.severity == Severity.ERROR]

    assert ok is False
    assert len(errors) >= 1
    assert any("non conforme pour le semestre complet" in a.message.lower()
               for a in errors)


def test_partial_semester_only_info(make_semester_context):
    """
    Semestre partiel : on doit avoir une INFO de suivi,
    mais aucun ERROR même si la moyenne est hors cible.
    """
    rule = DureeJourMoyenneSemestreRule()

    regime_id = next(iter(REGIME_AVG_SERVICE_MINUTES.keys()))
    target = REGIME_AVG_SERVICE_MINUTES[regime_id]
    tol = REGIME_AVG_TOLERANCE_MINUTES

    minutes = target + tol + 60  # largement hors tolérance

    ctx = make_semester_context(
        year=2024,
        regime_id=regime_id,
        sem="S1",
        minutes_per_day=minutes,
        full_semester=False,
    )

    ok, alerts = rule.check(ctx)

    errors = [a for a in alerts if a.severity == Severity.ERROR]
    infos = [a for a in alerts if a.severity == Severity.INFO]

    assert ok is True
    assert len(errors) == 0
    assert any("période incomplète" in a.message.lower() for a in infos)


def test_s2_partial_s1_full_behaviour(make_agent, make_workday):
    """
    Contexte couvrant seulement S1 complètement et une partie de S2 :
    - S1 : contrôle strict (conforme)
    - S2 : info 'période incomplète'
    """
    rule = DureeJourMoyenneSemestreRule()

    regime_id = next(iter(REGIME_AVG_SERVICE_MINUTES.keys()))
    target = REGIME_AVG_SERVICE_MINUTES[regime_id]

    agent = make_agent(regime_id=regime_id)

    # Petit helper local pour calculer l'heure de fin à partir d'une base 08:00
    def end_time_for(minutes_per_day: int) -> tuple[str, str]:
        h1 = "08:00"
        start_minutes = 8 * 60
        end_total = (start_minutes + minutes_per_day) % (24 * 60)
        h = end_total // 60
        m = end_total % 60
        h2 = f"{h:02d}:{m:02d}"
        return h1, h2

    work_days = []

    # 1) S1 complet, conforme
    sem1_start = date(2024, 1, 1)
    sem1_end = date(2024, 6, 30)
    h1_s1, h2_s1 = end_time_for(target)

    current = sem1_start
    while current <= sem1_end:
        work_days.append(
            make_workday(
                jour=current,
                type_label="poste",
                h1=h1_s1,
                h2=h2_s1,
                agent=agent,
            )
        )
        current += timedelta(days=1)

    # 2) S2 partiel : juillet à septembre, avec durée plus longue
    sem2_partial_start = date(2024, 7, 1)
    sem2_partial_end = date(2024, 9, 30)
    h1_s2, h2_s2 = end_time_for(target + 60)

    current = sem2_partial_start
    while current <= sem2_partial_end:
        work_days.append(
            make_workday(
                jour=current,
                type_label="poste",
                h1=h1_s2,
                h2=h2_s2,
                agent=agent,
            )
        )
        current += timedelta(days=1)

    ctx = PlanningContext(agent=agent, work_days=work_days)

    ok, alerts = rule.check(ctx)

    errors = [a for a in alerts if a.severity == Severity.ERROR]
    infos = [a for a in alerts if a.severity == Severity.INFO]

    # Pas d'erreur sur S1 conforme ; S2 partiel → suivi seulement
    assert len(errors) == 0
    assert len(infos) >= 1
    assert any("conforme pour le semestre complet" in a.message.lower()
               for a in infos)
    assert any("période incomplète" in a.message.lower()
               for a in infos)
