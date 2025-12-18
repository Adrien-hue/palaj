from datetime import date, timedelta
from typing import Dict, List, Optional


from db.repositories.affectation_repo import AffectationRepository
from db.repositories.agent_repo import AgentRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.tranche_repo import TrancheRepository


from core.domain.entities import Affectation, Agent, Poste, Tranche

from core.domain.services.planning_validator import PlanningValidator

class PostePlanningGenerator:
    """
    Génère automatiquement un planning pour un poste donné.
    """

    def __init__(
            self,
            poste: Poste,
            agent_repo: AgentRepository,
            qualification_repo: QualificationRepository,
            tranche_repo: TrancheRepository,
            etat_jour_agent_repo: EtatJourAgentRepository,
            affectation_repo: AffectationRepository
    ):
        self.poste = poste
        self.agent_repo = agent_repo
        self.qualification_repo = qualification_repo
        self.tranche_repo = tranche_repo
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.affectation_repo = affectation_repo

        self.validator = PlanningValidator(
            affectation_repo=self.affectation_repo,
            etat_jour_agent_repo=self.etat_jour_agent_repo,
        )

    def generate(self, start_date: date, end_date: date, simulate: bool = True):
        """Génère les affectations du poste entre deux dates."""
        BOLD, RESET = "\033[1m", "\033[0m"
        CYAN, GREEN, YELLOW, RED, GRAY = "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[90m"

        print(f"\n{BOLD}{CYAN}🧠 Génération du planning pour le poste : {self.poste.nom}{RESET}")
        print(f"{GRAY}  → Période : {start_date} → {end_date}{RESET}")

        tranches = self.poste.get_tranches(self.tranche_repo)

        if not tranches:
            print(f"{RED}[WARNING] Aucune tranche trouvée pour le poste {self.poste.nom}.{RESET}")
            return

        # Vérifie qu'aucune tranche n'est None (cas de données incohérentes)
        invalid_tranches = [tid for tid in self.poste.tranche_ids if self.tranche_repo.get(tid) is None]
        if invalid_tranches:
            print(f"{RED}[WARNING] Attention : {len(invalid_tranches)} tranche(s) introuvable(s) pour le poste {self.poste.nom} : {invalid_tranches}{RESET}")
            # Filtrer uniquement les tranches valides
            tranches = [t for t in tranches if t is not None]

        if not tranches:
            print(f"{RED}[WARNING] Impossible de continuer : aucune tranche valide trouvée pour le poste {self.poste.nom}.{RESET}")
            return

        qualifications = self.qualification_repo.list_for_poste(self.poste.id)
        
        qualified_agents = []
        for q in qualifications:
            agent = q.get_agent(self.agent_repo)

            if agent is None:
                print(f"{RED}[WARNING]  Qualification invalide : agent introuvable pour {q}{RESET}")
                continue
            qualified_agents.append(agent)

        if not qualified_agents:
            print(f"{RED}[WARNING] Aucun agent qualifié valide trouvé pour le poste {self.poste.nom}.{RESET}")
            return
        
        existing_affectations = self.affectation_repo.list_all()

        nb_days = (end_date - start_date).days + 1
        total_created = 0

        affect_hours = {a.id: 0.0 for a in qualified_agents}
        affect_count = {a.id: 0 for a in qualified_agents}

        for day_offset in range(nb_days):
            jour = start_date + timedelta(days=day_offset)
            print(f"\n{BOLD}{CYAN}📅 {jour}{RESET}")

            besoins: Dict[Tranche, int] = self._compute_besoins(tranches, jour)

            if not besoins:
                print(f"{GRAY}  Aucun besoin de couverture ce jour-là.{RESET}")
                continue

            for tranche, nb_a_couvrir in besoins.items():
                print(f"{GREEN}  → Tranche {tranche.abbr} : {nb_a_couvrir} agent(s) à couvrir{RESET}")

                for _ in range(nb_a_couvrir):
                    available_agents = [
                        a for a in qualified_agents
                        if self.validator.affectation_service.can_assign(a, tranche, jour)
                    ]

                    if not available_agents:
                        print(f"{RED}    [WARNING] Aucun agent disponible pour {tranche.abbr}{RESET}")
                        continue

                    selected = min(
                        available_agents,
                        key=lambda a: (affect_hours[a.id], affect_count[a.id])
                    )

                    affect = Affectation(selected.id, tranche.id, jour)
                    existing_affectations.append(affect)
                    affect_hours[selected.id] += tranche.duree()
                    affect_count[selected.id] += 1
                    total_created += 1

                    print(f"{YELLOW}    + {selected.get_full_name()} affecté à {tranche.abbr}{RESET}")

                    if not simulate:
                        self.affectation_repo.create(affect)

        print(f"\n{BOLD}{GREEN}✅ Génération terminée pour {self.poste.nom}{RESET}")
        print(f"{GRAY}  → {total_created} nouvelles affectations créées{RESET}")
        if simulate:
            print(f"{YELLOW}  💡 Mode simulation (aucune écriture){RESET}")

    # -----------------------------------------------------------
    def _compute_besoins(self, tranches: List[Tranche], jour: date) -> Dict[Tranche, int]:
        """Calcule les besoins de couverture restants pour une journée donnée."""
        existing_affectations = self.affectation_repo.list_all()
        besoins: Dict[Tranche, int] = {}

        for tranche in tranches:
            deja_couvert = sum(
                1 for a in existing_affectations if a.tranche_id == tranche.id and a.jour == jour
            )
            restant = tranche.nb_agents_requis - deja_couvert
            if restant > 0:
                besoins[tranche] = restant

        return besoins
    
    def _count_consecutive_days(self, agent: Agent, jour: date, affectations: List[Affectation]) -> int:
        """Compte les jours consécutifs de travail avant la date donnée."""
        days = sorted(a.jour for a in affectations if a.agent_id == agent.id)
        if not days:
            return 0

        streak = 0
        for d in reversed(days):
            if (jour - d).days == streak + 1:
                streak += 1
            else:
                break
        return streak

    def _is_available(self, agent: Agent, jour: date, existing_affectations: List[Affectation]) -> bool:
        """Retourne True si l'agent est disponible selon ses contraintes RH."""
        # Déjà affecté ce jour-là ?
        if any(a.agent_id == agent.id and a.jour == jour for a in existing_affectations):
            return False

        # État du jour
        etat = next((e for e in self.etat_jour_agent_repo.list_for_agent(agent.id) if e.jour == jour), None)
        if etat and etat.type_jour != "poste":
            return False

        # Trop de jours consécutifs travaillés ?
        previous_days = [a.jour for a in existing_affectations if a.agent_id == agent.id]
        if previous_days:
            last_worked = max(previous_days)
            if (jour - last_worked).days == 1:
                # On peut décider d'autoriser jusqu'à 6 jours consécutifs
                if self._count_consecutive_days(agent, jour, existing_affectations) >= 6:
                    return False

        return True

    # -----------------------------------------------------------
    def print_summary(self, start_date: date, end_date: date):
        """Affiche un résumé du nombre d'affectations sur la période."""
        from collections import Counter
        affs = [
            a for a in self.affectation_repo.list_all()
            if start_date <= a.jour <= end_date and a.tranche_id in self.poste.tranche_ids
        ]

        counts = Counter([a.agent_id for a in affs])

        print(f"\n📊 {self.poste.nom} — résumé de la période {start_date} → {end_date}")
        print(f"  Total : {len(affs)} affectations")
        for agent_id, total in counts.items():
            agent = self.agent_repo.get(agent_id)
            if agent:
                print(f"   - {agent.get_full_name():25} : {total} affectations")