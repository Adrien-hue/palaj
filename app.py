from datetime import date, datetime
from db.database import JsonDatabase
from db import cache_manager

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.agent_repo import AgentRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.poste_repo import PosteRepository
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.regime_repo import RegimeRepository
from db.repositories.tranche_repo import TrancheRepository

from core.data_integrity_checker import DataIntegrityChecker

from core.agent_planning import AgentPlanning
from core.multi_poste_planning  import MultiPostePlanning
from core.poste_planning import PostePlanning

from core.planning.multi_poste_planning_generator import MultiPostePlanningGenerator

CHECK_DB_INTEGRITY = True
TEST_GENERATION_PLANNING_MULTIPLE = False
TEST_AGENT = True

db = JsonDatabase(debug=False)

affectation_repo = AffectationRepository(db)
agent_repo = AgentRepository(db)
etat_jour_agent_repo = EtatJourAgentRepository(db)
poste_repo = PosteRepository(db)
qualification_repo = QualificationRepository(db)
regime_repo = RegimeRepository(db)
tranche_repo = TrancheRepository(db)

# ---------------------------------------
# Vérification de l'intégrité des données
# ---------------------------------------
if CHECK_DB_INTEGRITY:
    data_integrity_checker = DataIntegrityChecker(
        agent_repo=agent_repo,
        poste_repo=poste_repo,
        tranche_repo=tranche_repo,
        qualification_repo=qualification_repo,
        affectation_repo=affectation_repo,
        etat_jour_agent_repo=etat_jour_agent_repo
    )

    data_integrity_checker.run_all_checks()

    data_integrity_checker.print_report()

if TEST_GENERATION_PLANNING_MULTIPLE:
    poste_gmj = poste_repo.get(4)
    poste_gml = poste_repo.get(5)

    if poste_gmj and poste_gml:
        planning_gm = MultiPostePlanningGenerator(
            postes=[poste_gmj, poste_gml],
            agent_repo=agent_repo,
            qualification_repo=qualification_repo,
            tranche_repo=tranche_repo,
            etat_jour_repo=etat_jour_agent_repo,
            affectation_repo=affectation_repo,
        )

        planning_gm.generate(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            simulate=True
        )
    else:
        print(f"[WARNING] Un ou plusieurs postes introuvables : {poste_gmj}, {poste_gml}")

if TEST_AGENT:
    agent = agent_repo.get(9)
    if agent:
        agent.get_qualifications(qualification_repo)
        agent.get_regime(regime_repo)

        agent.get_absences_jours(etat_jour_agent_repo)
        agent.get_conges_jours(etat_jour_agent_repo)
        agent.get_repos_jours(etat_jour_agent_repo)
        agent.get_travail_jours(etat_jour_agent_repo)
        agent.get_zcot_jours(etat_jour_agent_repo)

        print(agent)
    else:
        print(f"[WARNING] Agent introuvable : {agent}")
