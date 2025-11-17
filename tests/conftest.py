"""
Script de tests.
Exécution :
    pytest -v --maxfail=1 --disable-warnings

    pytest -v --maxfail=1 --disable-warnings --color=yes --durations=5
"""

# tests/conftest.py
import pytest
from datetime import date, time, timedelta

from core.domain.entities import Agent, EtatJourAgent, Tranche, TypeJour
from core.domain.models.work_day import WorkDay
from core.domain.contexts.planning_context import PlanningContext


# --- FIXTURES DE BASE -------------------------------------------------------

@pytest.fixture
def sample_agent() -> Agent:
    """Renvoie un agent de test générique."""
    return Agent(id=1000, nom="HOUEE", prenom="Adrien")


@pytest.fixture
def tranche_matin() -> Tranche:
    """Tranche matinée typique."""
    return Tranche(id=1, nom="MJ", heure_debut=time(6, 20), heure_fin=time(14, 5), poste_id=9999)


@pytest.fixture
def tranche_nuit() -> Tranche:
    """Tranche de nuit typique."""
    return Tranche(id=2, nom="NJ", heure_debut=time(22, 0), heure_fin=time(6, 20), poste_id=9999)


@pytest.fixture
def workday_poste(tranche_matin):
    """Retourne une journée travaillée classique."""
    return WorkDay(
        jour=date(2025, 1, 1),
        etat=EtatJourAgent(9, date(2025, 1, 1), TypeJour.POSTE),
        tranches=[tranche_matin],
    )


@pytest.fixture
def workday_repos():
    """Retourne une journée de repos."""
    return WorkDay(
        jour=date(2025, 1, 2),
        etat=EtatJourAgent(9, date(2025, 1, 2), TypeJour.REPOS),
        tranches=[],
    )


@pytest.fixture
def base_context(sample_agent, workday_poste, workday_repos) -> PlanningContext:
    """
    Construit un contexte simple sur 2 jours :
    - Jour 1 : travail matinée
    - Jour 2 : repos
    """
    return PlanningContext(
        agent=sample_agent,
        work_days=[workday_poste, workday_repos],
        date_reference=workday_poste.jour,
    )


# --- HELPERS UTILES ---------------------------------------------------------

@pytest.fixture
def make_tranche():
    """Fabrique rapide d’une tranche personnalisée."""
    def _make(nom="T", debut=(8, 0), fin=(17, 0), id=99):
        return Tranche(id=id, nom=nom, heure_debut=time(*debut), heure_fin=time(*fin), poste_id=9999)
    return _make


@pytest.fixture
def make_workday():
    """Fabrique rapide de WorkDay (travail ou repos)."""
    def _make(jour, type_jour=TypeJour.POSTE, tranches=None):
        return WorkDay(
            jour=jour,
            etat=EtatJourAgent(9, jour, type_jour),
            tranches=tranches or [],
        )
    return _make

@pytest.fixture
def make_context_with_gpt(sample_agent):
    """
    Fabrique un PlanningContext simulant une ou plusieurs Grandes Périodes de Travail (GPT)
    avec possibilité d'inclure des jours de ZCOT, d'absence ou de congé.
    
    ⚙️ Usage :
        context = make_context_with_gpt(agent)(5)
        context = make_context_with_gpt(agent)(pattern=["POSTE", "ZCOT", "ABSENCE", "POSTE"])
    """

    def _make(
        nb_jours: int | None = None,
        start_date: date = date(2025, 1, 1),
        pattern: list[str] | None = None,
        include_left_repos: bool = True,
        include_right_repos: bool = True,
    ) -> PlanningContext:
        work_days = []

        # --- Jour de repos avant la GPT
        if include_left_repos:
            work_days.append(
            WorkDay(
                jour=start_date,
                etat=EtatJourAgent(
                    agent_id=sample_agent.id,
                    jour=start_date,
                    type_jour=TypeJour.REPOS,
                ),
                tranches=[],
            )
        )

        # --- Déterminer le motif des jours de GPT
        if pattern:
            jours_gpt = pattern
        elif nb_jours:
            jours_gpt = ["POSTE"] * nb_jours
        else:
            raise ValueError("Il faut fournir soit nb_jours soit pattern.")

        # --- Construire les WorkDay correspondant à la GPT
        for i, t_jour in enumerate(jours_gpt, start=1):
            jour_courant = start_date + timedelta(days=i)
            type_enum = getattr(TypeJour, t_jour.upper())

            work_days.append(
                WorkDay(
                    jour=jour_courant,
                    etat=EtatJourAgent(
                        agent_id=sample_agent.id,
                        jour=jour_courant,
                        type_jour=type_enum,
                    ),
                    tranches=[],
                )
            )

        if include_right_repos:
            # --- Jour de repos après la GPT
            end_date = start_date + timedelta(days=len(jours_gpt) + 1)
            work_days.append(
                WorkDay(
                    jour=end_date,
                    etat=EtatJourAgent(
                        agent_id=sample_agent.id,
                        jour=end_date,
                        type_jour=TypeJour.REPOS,
                    ),
                    tranches=[],
                )
            )

        # --- Création du PlanningContext
        context = PlanningContext(
            agent=sample_agent,
            work_days=work_days,
            date_reference=start_date,
        )

        return context

    return _make

@pytest.fixture
def make_context_with_rest(sample_agent):
    def _make(nb_work_days: int, nb_rest_days_after: int = 0, start_date: date = date(2025, 1, 1)):
        work_days = []
        for i in range(nb_work_days):
            jour = start_date + timedelta(days=i)
            work_days.append(
                WorkDay(
                    jour=jour,
                    etat=EtatJourAgent(sample_agent.id, jour, TypeJour.POSTE),
                    tranches=[]
                )
            )

        for i in range(nb_rest_days_after):
            jour = start_date + timedelta(days=nb_work_days + i)
            work_days.append(
                WorkDay(
                    jour=jour,
                    etat=EtatJourAgent(sample_agent.id, jour, TypeJour.REPOS),
                    tranches=[]
                )
            )

        jour = start_date + timedelta(days=nb_work_days + nb_rest_days_after)
        work_days.append(
            WorkDay(
                jour=jour,
                etat=EtatJourAgent(sample_agent.id, jour, TypeJour.POSTE),
                tranches=[]
            )
        )

        return PlanningContext(agent=sample_agent, work_days=work_days, date_reference=start_date)
    return _make