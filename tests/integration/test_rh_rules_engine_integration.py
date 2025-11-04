import pytest
from datetime import date, time, timedelta
from types import SimpleNamespace

from core.rh_rules.rh_rules_engine import RHRulesEngine
from core.rh_rules import AmplitudeMaxRule, ReposDoubleRule, GrandePeriodeTravailRule
from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities.work_day import WorkDay
from core.domain.entities import TypeJour

class FakeTranche:
    """Fausse tranche minimaliste utilisée dans les WorkDay de test."""
    def __init__(self, debut: time, fin: time):
        self.debut = debut
        self.fin = fin

    def duree_minutes(self) -> int:
        """Retourne la durée totale en minutes (gère le passage minuit)."""
        debut_dt = timedelta(hours=self.debut.hour, minutes=self.debut.minute)
        fin_dt = timedelta(hours=self.fin.hour, minutes=self.fin.minute)
        diff = (fin_dt - debut_dt).total_seconds() / 60
        if diff < 0:  # passage minuit
            diff += 24 * 60
        return int(diff)

@pytest.fixture
def simple_context():
    """
    Construit un PlanningContext cohérent :
    - 5 jours dont 3 travaillés
    - amplitude normale sur les jours travaillés
    - un repos entre deux blocs de travail
    """
    wd1 = WorkDay(jour=date(2025, 1, 1), etat=SimpleNamespace(type_jour=TypeJour.POSTE))
    wd2 = WorkDay(jour=date(2025, 1, 2), etat=SimpleNamespace(type_jour=TypeJour.POSTE))
    wd3 = WorkDay(jour=date(2025, 1, 3), etat=SimpleNamespace(type_jour=TypeJour.REPOS))
    wd4 = WorkDay(jour=date(2025, 1, 4), etat=SimpleNamespace(type_jour=TypeJour.POSTE))
    wd5 = WorkDay(jour=date(2025, 1, 5), etat=SimpleNamespace(type_jour=TypeJour.POSTE))

    fake_tranche = FakeTranche(time(8, 0), time(16, 0))
    for wd in [wd1, wd2, wd4, wd5]:
        wd.tranches = [fake_tranche]
    wd3.tranches = []

    ctx = PlanningContext(agent=SimpleNamespace(id=1), work_days=[wd1, wd2, wd3, wd4, wd5])
    return ctx


def test_rh_engine_with_real_rules(simple_context, capsys):
    """
    Teste l'exécution du moteur RH complet avec plusieurs vraies règles :
    - AmplitudeMaxRule (jour)
    - RuleGrandePeriodeTravail (période)
    - RuleReposDouble (période)
    """

    engine = RHRulesEngine(
        rules=[
            AmplitudeMaxRule(),
            GrandePeriodeTravailRule(),
            ReposDoubleRule(),
        ],
        verbose=True,
    )

    is_valid, alerts = engine.run_for_context(simple_context)

    out = capsys.readouterr().out
    assert "RAPPORT GLOBAL RÈGLES RH" in out
    assert isinstance(is_valid, bool)
    assert isinstance(alerts, list)

    # Le contexte doit être globalement valide (aucune erreur)
    assert is_valid


def test_rh_engine_detects_amplitude_error(capsys):
    """Vérifie qu'une amplitude excessive génère une alerte ERROR."""
    wd = WorkDay(jour=date(2025, 1, 1), etat=SimpleNamespace(type_jour=TypeJour.POSTE))
    wd.tranches = [FakeTranche(time(6, 0), time(23, 30))]  # ~17.5h
    ctx = PlanningContext(agent=SimpleNamespace(id=1), work_days=[wd])

    engine = RHRulesEngine(
        rules=[AmplitudeMaxRule()],
        verbose=True,
    )

    is_valid, alerts = engine.run_for_context(ctx)

    assert not is_valid
    assert any(a.severity.name == "ERROR" for a in alerts)

    out = capsys.readouterr().out
    assert "Amplitude" in out or "RAPPORT GLOBAL" in out