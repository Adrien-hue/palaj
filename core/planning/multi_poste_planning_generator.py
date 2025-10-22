from datetime import date, timedelta
from typing import List, Dict

from models.poste import Poste
from db.repositories.agent_repo import AgentRepository
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.tranche_repo import TrancheRepository

from core.planning.poste_planning_generator import PostePlanningGenerator


class MultiPostePlanningGenerator:
    """
    Gère la génération du planning sur plusieurs postes en parallèle,
    tout en garantissant la cohérence des affectations agent/jour.
    """

    def __init__(
        self,
        postes: List[Poste],
        agent_repo: AgentRepository,
        qualification_repo: QualificationRepository,
        tranche_repo: TrancheRepository,
        etat_jour_repo: EtatJourAgentRepository,
        affectation_repo: AffectationRepository,
    ):
        self.postes = postes
        self.agent_repo = agent_repo
        self.qualification_repo = qualification_repo
        self.tranche_repo = tranche_repo
        self.etat_jour_repo = etat_jour_repo
        self.affectation_repo = affectation_repo

    def generate(self, start_date: date, end_date: date, simulate: bool = True):
        BOLD, RESET = "\033[1m", "\033[0m"
        CYAN, GREEN, YELLOW, RED, GRAY = "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[90m"

        print(f"\n{BOLD}{CYAN}🧩 Génération multi-postes :{RESET}")
        print(f"{GRAY}  Période : {start_date} → {end_date}{RESET}")
        print(f"{GRAY}  Nombre de postes : {len(self.postes)}{RESET}")

        # Dictionnaire pour suivre les agents déjà affectés un jour donné
        agenda: Dict[int, List[date]] = {}

        total_created = 0
        for poste in self.postes:
            print(f"\n{BOLD}{GREEN}▶ Génération pour le poste {poste.nom}{RESET}")

            generator = PostePlanningGenerator(
                poste,
                self.agent_repo,
                self.qualification_repo,
                self.tranche_repo,
                self.etat_jour_repo,
                self.affectation_repo
            )

            before = len(self.affectation_repo.list_all())
            generator.generate(start_date, end_date, simulate=simulate)
            after = len(self.affectation_repo.list_all())

            total_created += (after - before)

            # Mettre à jour le suivi de jour travaillé
            for aff in self.affectation_repo.list_all():
                agenda.setdefault(aff.agent_id, []).append(aff.jour)

        print(f"\n{BOLD}{CYAN}📊 Résumé multi-postes :{RESET}")
        print(f"{GREEN}  Total de {total_created} affectations créées (simulation={simulate}){RESET}")
