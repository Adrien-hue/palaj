import datetime
import pytest

from core.domain.entities import Affectation, Agent, EtatJourAgent, Poste, Qualification, Regime, Tranche, TypeJour

from core.domain.services.agent_validator_service import AgentValidatorService
from core.domain.services.affectation_validator_service import AffectationValidatorService

from core.domain.services.poste_validator_service import PosteValidatorService
from core.domain.services.qualification_validator_service import (
    QualificationValidatorService,
)
from core.domain.services.regime_validator_service import RegimeValidatorService
from core.domain.services.tranche_validator_service import TrancheValidatorService
from core.domain.contexts.planning_context import PlanningContext
from core.utils.domain_alert import Severity


@pytest.fixture
def sample_date():
    return datetime.date(2024, 6, 1)


# AgentValidatorService

def test_agent_validator_detects_all_missing_fields(sample_date):
    agent = Agent(id=1, nom=" ", prenom="", regime_id=None)
    is_valid, alerts = AgentValidatorService().validate(agent)

    assert is_valid is False
    severities = {a.severity for a in alerts}
    assert Severity.ERROR in severities
    assert Severity.WARNING in severities
    assert any("aucun état journalier" in a.message.lower() for a in alerts)
    assert any("nom manquant" in a.message for a in alerts)
    assert any("régime" in a.message.lower() for a in alerts)
    assert any("aucun état" in a.message.lower() for a in alerts)


def test_agent_validator_global_duplicate_and_child_errors(sample_date):
    agent_one = Agent(id=1, nom="Dupont", prenom="Jean", regime_id=1)
    agent_duplicate = Agent(id=1, nom="Martin", prenom="Paul", regime_id=None)

    is_valid, alerts = AgentValidatorService().validate_all([agent_one, agent_duplicate])

    assert is_valid is False
    assert any("doublon" in a.message.lower() for a in alerts)
    assert any(a.severity == Severity.WARNING for a in alerts)


# AffectationValidatorService

def test_affectation_validator_flags_missing_fields_and_dates(sample_date):
    affectation = Affectation(agent_id=None, tranche_id=None, jour=sample_date) # pyright: ignore[reportArgumentType]
    is_valid, alerts = AffectationValidatorService().validate(affectation)

    assert is_valid is False
    messages = " ".join(a.message for a in alerts)
    assert "sans agent" in messages.lower()
    assert "sans tranche" in messages.lower()


def test_affectation_validator_future_and_past_dates(sample_date):
    too_old = Affectation(agent_id=1, tranche_id=2, jour=datetime.date(1990, 1, 1))
    too_future = Affectation(agent_id=1, tranche_id=2, jour=datetime.date.today() + datetime.timedelta(days=1000))

    _, old_alerts = AffectationValidatorService().validate(too_old)
    _, future_alerts = AffectationValidatorService().validate(too_future)

    assert any(a.severity == Severity.WARNING for a in old_alerts)
    assert any("futur" in a.message.lower() for a in future_alerts)


def test_affectation_validator_global_duplicate(sample_date):
    one = Affectation(agent_id=1, tranche_id=1, jour=sample_date)
    dup = Affectation(agent_id=1, tranche_id=2, jour=sample_date)

    is_valid, alerts = AffectationValidatorService().validate_all([one, dup])

    assert is_valid is False
    assert any("doublon" in a.message.lower() for a in alerts)


# EtatJourAgentValidatorService

def test_etat_jour_validator_rejects_invalid_type(sample_date):
    etat = EtatJourAgent(agent_id=1, jour=sample_date, type_jour="INVALID", description="") # pyright: ignore[reportArgumentType]
    etat_none = EtatJourAgent(agent_id=2, jour=sample_date, type_jour=None, description="") # pyright: ignore[reportArgumentType]
    is_valid, alerts = EtatJourAgentValidatorService().validate_all([etat, etat_none])

    assert is_valid is False
    assert any("sans type_jour" in a.message.lower() for a in alerts)
    assert any("type d'état inconnu" in a.message.lower() for a in alerts)


def test_etat_jour_validator_global_duplicate_and_missing_fields(sample_date):
    missing = EtatJourAgent(agent_id=None, jour=None, type_jour=TypeJour.POSTE, description="") # pyright: ignore[reportArgumentType]
    duplicate = EtatJourAgent(agent_id=2, jour=sample_date, type_jour=TypeJour.REPOS, description="")
    duplicate_same_day = EtatJourAgent(agent_id=2, jour=sample_date, type_jour=TypeJour.REPOS, description="")

    is_valid, alerts = EtatJourAgentValidatorService().validate_all([
        missing,
        duplicate,
        duplicate_same_day,
    ])

    assert is_valid is False
    assert any(a.severity == Severity.ERROR and "doublon" in a.message.lower() for a in alerts)
    assert any("sans agent_id" in a.message.lower() for a in alerts)
    assert any("sans date" in a.message.lower() for a in alerts)


# PosteValidatorService

def test_poste_validator_warnings_for_empty_relations():
    poste = Poste(id=1, nom="Accueil")
    
    is_valid, alerts = PosteValidatorService().validate(poste)

    assert is_valid is True
    assert any(a.severity == Severity.WARNING for a in alerts)
    assert any("aucune tranche" in a.message.lower() for a in alerts)


def test_poste_validator_detects_duplicate_and_mismatched_qualification():
    tranche = Tranche(id=1, nom="Matin", heure_debut="08:00", heure_fin="12:00", poste_id=1)
    good = Poste(id=1, nom="Accueil")
    good.set_tranches([tranche])
    bad_qualification = Qualification(agent_id=1, poste_id=99, date_qualification=datetime.date(2020, 1, 1))
    dupe = Poste(id=1, nom="Backup")
    dupe.set_qualifications([bad_qualification])

    is_valid, alerts = PosteValidatorService().validate_all([good, dupe])

    assert is_valid is False
    assert any("doublon" in a.message.lower() for a in alerts)
    assert any("incohérente" in a.message.lower() for a in alerts)


# QualificationValidatorService

def test_qualification_validator_missing_links_and_temporal_bounds(sample_date):
    missing_links = Qualification(agent_id=None, poste_id=None, date_qualification=datetime.date(1940, 1, 1)) # pyright: ignore[reportArgumentType]
    future = Qualification(agent_id=1, poste_id=1, date_qualification=datetime.date.today() + datetime.timedelta(days=1))

    _, missing_alerts = QualificationValidatorService().validate(missing_links)
    _, future_alerts = QualificationValidatorService().validate(future)

    assert any("sans agent" in a.message.lower() for a in missing_alerts)
    assert any("sans poste" in a.message.lower() for a in missing_alerts)
    assert any("incohérente" in a.message.lower() for a in missing_alerts)
    assert any("future" in a.message.lower() for a in future_alerts)


def test_qualification_validator_global_duplicate_detection(sample_date):
    q1 = Qualification(agent_id=1, poste_id=2, date_qualification=sample_date)
    q2 = Qualification(agent_id=1, poste_id=2, date_qualification=sample_date)

    is_valid, alerts = QualificationValidatorService().validate_all([q1, q2])

    assert is_valid is False
    assert any("doublon" in a.message.lower() for a in alerts)


# RegimeValidatorService

def test_regime_validator_catches_invalid_durations_and_repos():
    regime = Regime(id=1, nom="Test", duree_moyenne_journee_service_min=None, repos_periodiques_annuels=1000) # pyright: ignore[reportArgumentType]
    regime_bis = Regime(id=2, nom="Test bis", duree_moyenne_journee_service_min=1500, repos_periodiques_annuels=0) # pyright: ignore[reportArgumentType]
    is_valid, alerts = RegimeValidatorService().validate_all([regime, regime_bis])

    assert is_valid is False
    assert any("durée moyenne impossible" in a.message.lower() for a in alerts)
    assert any("durée moyenne" in a.message.lower() for a in alerts)
    assert any("365" in a.message for a in alerts)


def test_regime_validator_duplicate_and_warning_repos():
    base = Regime(id=1, nom="Normal", duree_moyenne_journee_service_min=480, repos_periodiques_annuels=None) # pyright: ignore[reportArgumentType]
    duplicate = Regime(id=1, nom="normal", duree_moyenne_journee_service_min=480, repos_periodiques_annuels=10)

    is_valid, alerts = RegimeValidatorService().validate_all([base, duplicate])

    assert is_valid is False
    assert any(a.severity == Severity.ERROR and "doublon" in a.message.lower() for a in alerts)
    assert any(a.severity == Severity.WARNING for a in alerts)


# TrancheValidatorService

def test_tranche_validator_flags_duration_and_missing_poste():
    tranche = Tranche(id=1, nom="Nulle", heure_debut="08:00", heure_fin="08:00", poste_id=None) # pyright: ignore[reportArgumentType]
    is_valid, alerts = TrancheValidatorService().validate(tranche)

    assert is_valid is False
    assert any("durée nulle" in a.message.lower() for a in alerts)
    assert any("aucun poste" in a.message.lower() for a in alerts)


def test_tranche_validator_detects_duplicate_and_long_duration():
    long_tranche = Tranche(id=1, nom="Longue", heure_debut="00:00", heure_fin="14:00", poste_id=1)
    duplicate = Tranche(id=1, nom="Copie", heure_debut="06:00", heure_fin="07:00", poste_id=1)
    invalide_tranche = Tranche(id=2, nom="Invalide", heure_debut=None, heure_fin="12:00", poste_id=1) # pyright: ignore[reportArgumentType]

    is_valid, alerts = TrancheValidatorService().validate_all([long_tranche, duplicate, invalide_tranche])

    assert is_valid is False
    assert any(a.severity == Severity.WARNING for a in alerts)
    assert any(a.severity == Severity.ERROR and "doublon" in a.message.lower() for a in alerts)