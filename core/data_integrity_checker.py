# core/data_integrity_checker.py
from typing import List, Tuple, Set

from core.domain.services.affectation_service import AffectationService
from core.domain.services.tranche_service import TrancheService

from db.repositories.agent_repo import AgentRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.poste_repo import PosteRepository
from db.repositories.tranche_repo import TrancheRepository
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.affectation_repo import AffectationRepository


class DataIntegrityChecker:
    """
    Vérifie la cohérence globale des données chargées dans le système :
    - doublons
    - clés étrangères invalides
    - références manquantes entre entités
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        poste_repo: PosteRepository,
        tranche_repo: TrancheRepository,
        qualification_repo: QualificationRepository,
        affectation_repo: AffectationRepository,
        etat_jour_agent_repo: EtatJourAgentRepository
    ):
        self.agent_repo = agent_repo
        self.poste_repo = poste_repo
        self.tranche_repo = tranche_repo
        self.qualification_repo = qualification_repo
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.affectation_repo = affectation_repo

        # Pour stocker les erreurs détectées
        self.errors: List[str] = []
        self.warnings: List[str] = []

    # ---------- Vérifications principales ----------

    def check_agents(self):
        """Vérifie les doublons et champs manquants sur les agents."""
        seen_ids: Set[int] = set()
        for agent in self.agent_repo.list_all():
            if agent.id in seen_ids:
                self.errors.append(f"❌ Doublon d'agent ID {agent.id} ({agent.get_full_name()})")
            seen_ids.add(agent.id)

            if not agent.nom or not agent.prenom:
                self.warnings.append(f"⚠️ Agent ID {agent.id} avec nom ou prénom manquant")

    def check_affectations_vs_etat(self, etat_jour_agent_repo):
        """Vérifie qu'une affectation n'entre pas en conflit avec un état d'agent."""
        for a in self.affectation_repo.list_all():
            etat = etat_jour_agent_repo.get_for_agent_and_day(a.agent_id, a.jour)
            if etat and etat.type_jour in ("repos", "conge", "absence"):
                self.errors.append(
                    f"❌ Affectation {a.id} pour agent {a.agent_id} le {a.jour} "
                    f"entre en conflit avec un jour '{etat.type_jour}'"
                )

    def check_postes(self):
        """Vérifie les doublons et tranches inexistantes dans les postes."""
        seen_ids: Set[int] = set()
        for poste in self.poste_repo.list_all():
            if poste.id in seen_ids:
                self.errors.append(f"❌ Doublon de poste ID {poste.id} ({poste.nom})")
            seen_ids.add(poste.id)

            for tid in poste.tranche_ids:
                if not self.tranche_repo.get(tid):
                    self.errors.append(
                        f"❌ Poste {poste.nom} référence une tranche inexistante (id={tid})"
                    )

    def check_tranches(self):
        """Vérifie les doublons et la validité des tranches."""
        service = TrancheService(self.tranche_repo, verbose=True)
        
        is_valid, alerts = service.validate_all()
        
        if not is_valid:
            self.errors.extend(alerts)

    def check_qualifications(self):
        """Vérifie que chaque qualification référence un agent et un poste existant."""
        for q in self.qualification_repo.list_all():
            if not self.agent_repo.get(q.agent_id):
                self.errors.append(f"❌ Qualification {q.id} référence agent inexistant {q.agent_id}")
            if not self.poste_repo.get(q.poste_id):
                self.errors.append(f"❌ Qualification {q.id} référence poste inexistant {q.poste_id}")

    def check_affectations(self):
        """Vérifie que chaque affectation référence un agent et une tranche existants."""
        service = AffectationService(self.agent_repo, self.affectation_repo, self.etat_jour_agent_repo, self.tranche_repo, verbose=True)

        is_valid, alerts = service.validate_all()
        
        if not is_valid:
            self.errors.extend(alerts)

    # ---------- Méthodes utilitaires ----------

    def run_all_checks(self) -> bool:
        """
        Exécute l'ensemble des vérifications.
        Retourne True si tout est cohérent, False sinon.
        """
        self.errors.clear()
        self.warnings.clear()

        self.check_agents()
        self.check_postes()
        self.check_tranches()
        self.check_qualifications()
        self.check_affectations()

        return len(self.errors) == 0

    def print_report(self):
        """Affiche un résumé lisible et coloré des erreurs et avertissements."""
        RESET, RED, YELLOW, GREEN, CYAN = "\033[0m", "\033[91m", "\033[93m", "\033[92m", "\033[96m"

        print(f"\n{CYAN}🧪 === Rapport d'intégrité des données ==={RESET}")
        if not self.errors and not self.warnings:
            print(f"{GREEN}✅ Aucune anomalie détectée.{RESET}")
            return

        if self.errors:
            print(f"\n{RED}❌ Erreurs critiques :{RESET}")
            for e in self.errors:
                print(f"  - {e}")

        if self.warnings:
            print(f"\n{YELLOW}⚠️ Avertissements :{RESET}")
            for w in self.warnings:
                print(f"  - {w}")

        print(f"\n{CYAN}--- Fin du rapport ---{RESET}\n")

