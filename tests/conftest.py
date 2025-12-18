"""
Script de tests.
Exécution :
    pytest -v --maxfail=1 --disable-warnings

    pytest -v --maxfail=1 --disable-warnings --color=yes --durations=5
"""

# tests/conftest.py
from pathlib import Path
from datetime import date, time, timedelta

import pytest

from core.domain.entities import Affectation, Agent, EtatJourAgent, Tranche, TypeJour
from core.domain.models.work_day import WorkDay
from core.domain.contexts.planning_context import PlanningContext

# ====================
# Factories génériques
# ====================

@pytest.fixture
def make_affectation():
    """
    Factory pour créer une Affectation simpl.
    Usage dans un test :
        afffectation = make_affectation(agent_id=1, tranche_id=42)
    """
    def _make(
        agent_id: int = 1000,
        tranche_id: int = 1000,
        jour = date(2025, 1, 1),
    ) -> Affectation:
        return Affectation(
            agent_id=agent_id,
            tranche_id=tranche_id,
            jour=jour,
        )

    return _make

@pytest.fixture
def make_agent():
    """
    Factory pour créer un Agent simple, en contrôlant facilement le regime_id.
    Usage dans un test :
        agent = make_agent(regime_id=1, id=42)
    """
    def _make(
        regime_id: int | None = None,
        id: int = 1000,
        nom: str = "HOUEE",
        prenom: str = "Adrien",
        code_personnel: str = "X001",
    ) -> Agent:
        return Agent(
            id=id,
            nom=nom,
            prenom=prenom,
            code_personnel=code_personnel,
            regime_id=regime_id,
        )

    return _make

@pytest.fixture
def make_context(make_agent, make_workday):
    """
    Fabrique un PlanningContext avec une ou plusieurs GPT consécutives.

    Paramètres possibles :
      - nb_jours : nombre de jours dans la GPT (si pattern est None)
      - pattern : liste de labels ["POSTE", "ZCOT", "ABSENCE", ...]
      - start_date : début du contexte
      - include_left_repos : ajoute un REPOS avant la GPT
      - include_right_repos : ajoute un REPOS après la GPT
    """

    def _make(
        nb_jours: int | None = None,
        pattern: list[str] | None = None,
        start_date: date = date(2025, 1, 1),
        include_left_repos: bool = True,
        include_right_repos: bool = True,
    ) -> PlanningContext:
        work_days: list[WorkDay] = []

        # Repos avant la GPT
        if include_left_repos:
            work_days.append(
                make_workday(
                    jour=start_date,
                    type_label="repos",
                )
            )

        # Déterminer le pattern des jours "en GPT"
        if pattern is not None:
            labels = pattern
        elif nb_jours is not None:
            labels = ["POSTE"] * nb_jours
        else:
            raise ValueError("Il faut fournir soit nb_jours soit pattern à make_context_with_gpt().")

        # GPT : jours consécutifs à partir de start_date + 1
        for i, label in enumerate(labels, start=1):
            jour = start_date + timedelta(days=i)
            work_days.append(
                make_workday(
                    jour=jour,
                    type_label=label.lower(),  # make_workday accepte "poste", "zcot", ...
                )
            )

        # Repos après la GPT
        if include_right_repos:
            last_day = start_date + timedelta(days=len(labels) + 1)
            work_days.append(
                make_workday(
                    jour=last_day,
                    type_label="repos",
                )
            )

        ctx = PlanningContext(
            agent=make_agent(),
            work_days=work_days,
            date_reference=start_date,
        )
        return ctx

    return _make

@pytest.fixture
def make_context_single_day(make_agent, make_workday):
    """
    Construit un PlanningContext pour UNE seule journée,
    en se basant sur make_workday pour créer le WorkDay.
    """
    from core.domain.contexts.planning_context import PlanningContext

    def _make(
        jour: date = date(2025, 1, 1),
        type_label: str = "poste",
        nocturne: bool = False,
        h1: time | str | None = None,
        h2: time | str | None = None,
    ) -> PlanningContext:
        wd = make_workday(
            jour=jour,
            type_label=type_label,
            nocturne=nocturne,
            h1=h1,
            h2=h2,
        )
        return PlanningContext(
            agent=make_agent(),
            work_days=[wd],
            date_reference=jour,
        )

    return _make

@pytest.fixture
def make_semester_context(make_workday, make_agent):
    """
    Construit un PlanningContext pour un semestre :
    - sem: "S1" ou "S2"
    - minutes_per_day : durée souhaitée
    - full_semester : complet ou partiel
    """

    def _make(
        year: int,
        regime_id: int,
        sem: str = "S1",
        minutes_per_day: int = 480,
        full_semester: bool = True,
    ) -> PlanningContext:
        agent = make_agent(regime_id=regime_id)

        # Début / fin du semestre
        if sem == "S1":
            sem_start = date(year, 1, 1)
            sem_end = date(year, 6, 30)
        else:
            sem_start = date(year, 7, 1)
            sem_end = date(year, 12, 31)

        # Calcul automatique de h2 à partir d'une base 08:00
        start_minutes = 8 * 60
        end_total = (start_minutes + minutes_per_day) % (24 * 60)
        h = end_total // 60
        m = end_total % 60
        h1 = "08:00"
        h2 = f"{h:02d}:{m:02d}"

        work_days = []

        if full_semester:
            current = sem_start
            while current <= sem_end:
                work_days.append(
                    make_workday(
                        jour=current,
                        type_label="poste",
                        h1=h1,
                        h2=h2,
                        agent=agent,
                    )
                )
                current += timedelta(days=1)
        else:
            # Semestre partiel : ~ mars → mai (~60 jours)
            start = sem_start + timedelta(days=60)
            end = min(sem_end, start + timedelta(days=60))
            current = start
            while current <= end:
                work_days.append(
                    make_workday(
                        jour=current,
                        type_label="poste",
                        h1=h1,
                        h2=h2,
                        agent=agent,
                    )
                )
                current += timedelta(days=1)

        return PlanningContext(agent=agent, work_days=work_days)

    return _make

@pytest.fixture
def make_year_context_conges(make_agent, make_workday):
    """
    Construit un contexte couvrant l'année complète (1/1 → 31/12)
    avec des jours de congés facultatifs.
    """

    def _make(year: int, conge_days: list[date], regime_id: int | None = None):
        agent = make_agent(regime_id=regime_id)
        work_days = []

        # Sentinelles pour couvrir l'année
        work_days.append(make_workday(date(year, 1, 1), type_label="poste", agent=agent))
        work_days.append(make_workday(date(year, 12, 31), type_label="poste", agent=agent))

        # Ajouter les congés
        for d in conge_days:
            work_days.append(make_workday(d, type_label="conge", agent=agent))

        return PlanningContext(agent=agent, work_days=work_days)

    return _make

@pytest.fixture
def make_repos_context(make_agent, make_workday):
    """
    Construit un PlanningContext avec des jours de REPOS répartis sur une période.

    - dates_repos : liste de dates à marquer comme REPOS
    - regime_id   : optionnel, pour enrichir l'agent
    - full_year   : si True, on couvre du 1/1 au 31/12 de l'année indiquée
                    et on met REPOS uniquement sur dates_repos, POSTE sinon.
      sinon : on couvre de min(dates_repos) à max(dates_repos).

    Si dates_repos est vide et full_year=False -> contexte sans WorkDay.
    """

    def _make(
        dates_repos: list[date],
        regime_id: int | None = None,
        full_year: bool = False,
        year: int | None = None,
    ) -> PlanningContext:
        agent = make_agent(regime_id=regime_id)
        work_days: list[WorkDay] = []

        if full_year:
            if year is None:
                if not dates_repos:
                    raise ValueError("full_year=True mais ni year ni dates fournis.")
                year = dates_repos[0].year

            start = date(year, 1, 1)
            end = date(year, 12, 31)

            current = start
            while current <= end:
                type_label = "repos" if current in dates_repos else "poste"
                wd = make_workday(
                    jour=current,
                    type_label=type_label,
                    agent=agent,
                )
                work_days.append(wd)
                current += timedelta(days=1)

            return PlanningContext(
                agent=agent,
                work_days=work_days,
                date_reference=start,
            )

        # --- Période minimale (non full-year)
        if not dates_repos:
            return PlanningContext(
                agent=agent,
                work_days=[],
                date_reference=None,
            )

        start = min(dates_repos)
        end = max(dates_repos)

        current = start
        while current <= end:
            type_label = "repos" if current in dates_repos else "poste"
            wd = make_workday(
                jour=current,
                type_label=type_label,
                agent=agent,
            )
            work_days.append(wd)
            current += timedelta(days=1)

        return PlanningContext(
            agent=agent,
            work_days=work_days,
            date_reference=start,
        )

    return _make


@pytest.fixture
def make_etat_jour_agent():
    """
    Factory pour créer un EtatJourAgent simple.
    Usage dans un test :
        etat_jour_agent = make_etat_jour_agent(type_jour=TypeJour.REPOS)
    """
    def _make(
        agent_id = 1000,
        jour = date(2025, 1, 1),
        type_jour = TypeJour.ZCOT,
        description = "Un jour en ZCOT",
    ) -> EtatJourAgent:
        return EtatJourAgent(
            agent_id=agent_id,
            jour=jour,
            type_jour=type_jour,
            description=description,
        )

    return _make

@pytest.fixture
def make_planning_like():
    """
    Fabrique un objet 'planning-like' avec les 3 méthodes
    attendues par PlanningContext.from_planning :
    - get_agent()
    - get_work_days()
    - get_start_date()
    """
    class _FakePlanning:
        def __init__(self, agent, work_days, start_date):
            self._agent = agent
            self._work_days = work_days
            self._start_date = start_date

        def get_agent(self):
            return self._agent

        def get_work_days(self):
            return self._work_days

        def get_start_date(self):
            return self._start_date

    def _factory(agent, work_days, start_date):
        return _FakePlanning(agent, work_days, start_date)

    return _factory

@pytest.fixture
def make_tranche():
    """
    Factory pour créer une Tranche simple, en contrôlant facilement le poste_id.
    Usage dans un test :
        tanche = make_tranche(poste_id=1, nom="Tranche M")
    """
    def _make(
        id: int = 1000,
        nom: str = "Tranche",
        heure_debut: time | str = time(hour=8, minute=0),
        heure_fin: time | str = time(hour=16, minute=0),
        poste_id: int = 9999,
    ) -> Tranche:
        return Tranche(
            id=id,
            nom=nom,
            heure_debut=heure_debut,
            heure_fin=heure_fin,
            poste_id=poste_id
        )

    return _make

@pytest.fixture
def make_workday(make_agent, make_tranche, make_etat_jour_agent):
    """
    Factory générique pour construire un WorkDay cohérent.

    type_label :
      - "poste"  → WorkDay avec tranche(s) (jour de service classique)
      - "zcot"   → WorkDay avec EtatJourAgent ZCOT
      - "repos"  → WorkDay de repos (EtatJourAgent REPOS)
      - "conge"  → WorkDay de congé
      - "absence"→ WorkDay d'absence
      - autre    → WorkDay avec un EtatJourAgent de ce type (si Enum valide)

    nocturne=True → pour type "poste", utilise une tranche de nuit 22h-6h
                    (surchargable par h1/h2).
    """

    def _make(
        jour: date,
        agent: Agent | None = None,
        type_label: str = "poste",
        nocturne: bool = False,
        h1: time | str | None = None,
        h2: time | str | None = None,
    ) -> WorkDay:
        etat: EtatJourAgent | None = None
        tranches: list[Tranche] = []

        agent = agent or make_agent

        label = type_label.lower()

        # --- Journée POSTE (avec tranches) ---
        if label == "poste":
            # valeurs par défaut
            if nocturne:
                debut = h1 or "22:00"
                fin = h2 or "06:00"
            else:
                debut = h1 or "08:00"
                fin = h2 or "10:00"

            tranches = [make_tranche(heure_debut=debut, heure_fin=fin)]
            # pas besoin d'etat : WorkDay.type() renvoie POSTE si tranches != []

        # --- ZCOT / REPOS / CONGE / ABSENCE : via EtatJourAgent ---
        elif label in ("zcot", "repos", "conge", "absence"):
            etat = make_etat_jour_agent(
                jour=jour,
                type_jour=getattr(TypeJour, label.upper()),
            )

        # --- Autre type → tentative générique ---
        else:
            # on essaie de construire un TypeJour(label)
            try:
                tj = TypeJour(label)
            except ValueError:
                tj = TypeJour.INCONNU
            etat = make_etat_jour_agent(jour=jour, type_jour=tj)

        return WorkDay(jour=jour, etat=etat, tranches=tranches)

    return _make