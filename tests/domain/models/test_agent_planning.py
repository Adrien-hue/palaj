from datetime import date, time

from core.domain.models.agent_planning import AgentPlanning
from core.domain.models.work_day import WorkDay
from core.domain.entities import (
    TypeJour,
)



# ------------------------------------------------------------
# TEST build()
# ------------------------------------------------------------

def test_build_basic(make_affectation, make_agent, make_etat_jour_agent, make_tranche):
    agent = make_agent()
    d1 = date(2025,1,1)
    d2 = date(2025,1,3)

    et1 = make_etat_jour_agent(date(2025,1,1), TypeJour.POSTE)
    et2 = make_etat_jour_agent(date(2025,1,2), TypeJour.REPOS)
    et3 = make_etat_jour_agent(date(2025,1,3), TypeJour.ZCOT)
    etats = [et1, et2, et3]

    t1 = make_tranche(10, time(8,0), time(12,0))
    affect = make_affectation(10, date(2025,1,1))
    affs = [affect]

    pl = AgentPlanning.build(
        agent=agent,
        start_date=d1,
        end_date=d2,
        etats=etats,
        affectations=affs,
        tranches_by_id={10: t1}
    )

    assert pl.agent is agent
    assert pl.start_date == d1
    assert pl.end_date == d2
    assert len(pl.work_days) == 3


def test_build_tranche_missing_is_skipped(make_affectation, make_agent, make_etat_jour_agent):
    """
    Si une affectation référence une tranche non fournie,
    elle ne doit pas crasher le build().
    """
    agent = make_agent()

    et = make_etat_jour_agent(date(2025,1,1), TypeJour.POSTE)
    aff = make_affectation(999, date(2025,1,1))  # tranche inconnue

    pl = AgentPlanning.build(
        agent,
        date(2025,1,1),
        date(2025,1,1),
        etats=[et],
        affectations=[aff],
        tranches_by_id={}  # vide
    )

    assert len(pl.work_days) == 1
    assert pl.work_days[0].tranches == []


# ------------------------------------------------------------
# GETTERS
# ------------------------------------------------------------

def test_getters_basic(make_agent):
    agent = make_agent()
    pl = AgentPlanning(
        agent=agent,
        start_date=date(2025,1,1),
        end_date=date(2025,1,10),
        etats=[],
        affectations=[],
        tranches=[],
        work_days=[]
    )

    assert pl.get_agent() is agent
    assert pl.get_start_date() == date(2025,1,1)
    assert pl.get_end_date() == date(2025,1,10)
    assert pl.get_nb_jours() == 10


# ------------------------------------------------------------
# ETATS (repos / congés / absences / zcot / travail)
# ------------------------------------------------------------

def test_etat_filters(make_agent, make_etat_jour_agent):
    et_repos = make_etat_jour_agent(jour=date(2025,1,1), type_jour=TypeJour.REPOS)
    et_conge = make_etat_jour_agent(jour=date(2025,1,2), type_jour=TypeJour.CONGE)
    et_abs = make_etat_jour_agent(jour=date(2025,1,3), type_jour=TypeJour.ABSENCE)
    et_zcot = make_etat_jour_agent(jour=date(2025,1,4), type_jour=TypeJour.ZCOT)
    et_poste = make_etat_jour_agent(jour=date(2025,1,5), type_jour=TypeJour.POSTE)

    pl = AgentPlanning(
        agent=make_agent(),
        start_date=date(2025,1,1),
        end_date=date(2025,1,5),
        etats=[et_repos, et_conge, et_abs, et_zcot, et_poste],
        affectations=[],
        tranches=[],
        work_days=[]
    )

    assert pl.get_repos_jours() == [et_repos]
    assert pl.get_conges_jours() == [et_conge]
    assert pl.get_absences_jours() == [et_abs]
    assert pl.get_zcot_jours() == [et_zcot]
    assert pl.get_travail_jours() == [et_poste]
    assert pl.get_all_etats() == [et_repos, et_conge, et_abs, et_zcot, et_poste]


# ------------------------------------------------------------
# DIMANCHES
# ------------------------------------------------------------

def test_dimanches_stats(make_agent, make_etat_jour_agent):
    # dimanche : 5 janvier 2025
    d1 = date(2025,1,1)
    d2 = date(2025,1,12)

    et_dim_trav = make_etat_jour_agent(jour=date(2025,1,5), type_jour=TypeJour.POSTE)
    pl = AgentPlanning(
        agent=make_agent(),
        start_date=d1,
        end_date=d2,
        etats=[et_dim_trav],
        affectations=[],
        tranches=[],
        work_days=[]
    )

    nb_trav, nb_total = pl.get_dimanches_stats()

    assert nb_total == 2  # dimanches : 5 et 12, mais end=10 → seulement 5 et  (2025-01-12 n'est pas inclus)
    assert nb_trav == 1


def test_dimanches_stats_zcot_counted(make_agent, make_etat_jour_agent):
    # dimanche 5 janvier
    et_z = make_etat_jour_agent(jour=date(2025,1,5), type_jour=TypeJour.ZCOT)
    pl = AgentPlanning(
        agent=make_agent(),
        start_date=date(2025,1,1),
        end_date=date(2025,1,10),
        etats=[et_z],
        affectations=[],
        tranches=[],
        work_days=[]
    )

    nb_trav, nb_total = pl.get_dimanches_stats()
    assert nb_trav == 1


# ------------------------------------------------------------
# TOTAL HEURES TRAVAILLÉES
# ------------------------------------------------------------

def test_total_heures_travaillees(make_affectation, make_agent, make_etat_jour_agent, make_tranche):
    j1 = date(2025,1,1)
    j2 = date(2025,1,2)

    # Tranche de 2 heures
    t1 = make_tranche(heure_debut=time(8), heure_fin=time(10))

    aff = make_affectation(j1)

    # ZCOT count = 8h fixes
    et_zcot = make_etat_jour_agent(jour=j2, type_jour=TypeJour.ZCOT)

    pl = AgentPlanning(
        agent=make_agent(),
        start_date=j1,
        end_date=j2,
        etats=[et_zcot],
        affectations=[aff],
        tranches=[t1],
        work_days=[]
    )

    assert pl.get_total_heures_travaillees() == 10  # 2h + 8h


def test_total_heures_no_match(make_affectation, make_agent):
    """Si une affectation pointe vers une tranche qui n’est pas dans self.tranches,
    la durée ne compte pas."""
    j1 = date(2025,1,1)
    aff = make_affectation(999, j1)  # inconnue

    pl = AgentPlanning(
        agent=make_agent(),
        start_date=j1,
        end_date=j1,
        etats=[],
        affectations=[aff],
        tranches=[],  # aucune tranche fournie
        work_days=[]
    )

    assert pl.get_total_heures_travaillees() == 0


# ------------------------------------------------------------
# ITER DAYS
# ------------------------------------------------------------

def test_iter_days(make_agent):
    d = date(2025,1,1)
    w1 = WorkDay(jour=d, etat=None, tranches=[])

    pl = AgentPlanning(
        agent=make_agent(),
        start_date=d,
        end_date=d,
        etats=[],
        affectations=[],
        tranches=[],
        work_days=[w1]
    )

    days = list(pl.iter_days())
    assert days == [w1]