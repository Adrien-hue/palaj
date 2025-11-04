# core/poste_planning.py
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Dict, Tuple
from datetime import date, timedelta

from tabulate import tabulate

from core.domain.entities import Affectation, Poste, Tranche

from db.repositories.tranche_repo import TrancheRepository
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.agent_repo import AgentRepository

class PostePlanning:
    """
    Vue d'ensemble d'un poste sur une période donnée.
    Permet d'analyser la couverture des tranches, les affectations par jour, etc.
    """

    def __init__(
        self,
        poste: Poste,
        start_date: date,
        end_date: date,
        affectation_repo: AffectationRepository,
        agent_repo: AgentRepository,
        tranche_repo: TrancheRepository,
    ):
        self.poste = poste
        self.tranche_repo = tranche_repo
        self.affectation_repo = affectation_repo
        self.agent_repo = agent_repo
        self.start_date = start_date
        self.end_date = end_date

        # Données chargées en lazy loading
        self._tranches = None
        self._affectations = None

    # --------------------------
    # Chargements / accès de base
    # --------------------------

    def get_affectations_for_day(self, jour: date) -> List[Affectation]:
        """
        Retourne les affectations de CE poste pour la date donnée.
        """
        return [aff for aff in self.get_affectations() if aff.jour == jour]

    def find_uncovered_shifts(self) -> List[Tuple[date, Tranche]]:
        """
        Retourne la liste des créneaux non couverts sous forme de tuples (jour, tranche).
        """
        tranches = self.get_tranches()
        covered = {(a.jour, a.tranche_id) for a in self.get_affectations()}

        res: List[Tuple[date, Tranche]] = []
        d = self.start_date
        while d <= self.end_date:
            for t in tranches:
                if (d, t.id) not in covered:
                    res.append((d, t))
            d += timedelta(days=1)
        return res

    # --------------------------
    # Chargements / accès de base
    # --------------------------

    def get_tranches(self):
        if self._tranches is None:
            self._tranches = self.poste.get_tranches(self.tranche_repo)
        return self._tranches

    def get_affectations(self):
        if self._affectations is None:
            all_affectations = self.affectation_repo.list_all()
            tranche_ids = {t.id for t in self.get_tranches()}
            self._affectations = [
                aff for aff in all_affectations
                if aff.tranche_id in tranche_ids and self.start_date <= aff.jour <= self.end_date
            ]
        return self._affectations

    # --------------------------
    # Analyses
    # --------------------------

    def get_total_theoretical_slots(self) -> int:
        """
        Nombre total de 'créneaux' à couvrir sur la période = nb_tranches * nb_jours.
        """
        nb_tranches = len(self.get_tranches())
        nb_jours = (self.end_date - self.start_date).days + 1
        return nb_tranches * nb_jours

    def get_coverage_rate(self) -> float:
        """
        Taux global de couverture de ce poste sur la période.
        """
        total_slots = self.get_total_theoretical_slots()
        if total_slots == 0:
            return 0.0
        nb_affectations = len(self.get_affectations())
        return round((nb_affectations / total_slots) * 100, 2)

    def get_daily_coverage(self) -> Dict[date, Dict]:
        """
        Retourne pour chaque jour un dict avec nb_tranches à couvrir / nb_tranches couvertes / agents affectés.
        """
        daily_data: Dict[date, Dict] = {}
        tranche_ids = {t.id for t in self.get_tranches()}

        current = self.start_date
        while current <= self.end_date:
            affs_today = [
                aff for aff in self.get_affectations() if aff.jour == current
            ]
            nb_covered = len(affs_today)
            nb_total = len(tranche_ids)
            agent_ids = {aff.agent_id for aff in affs_today}

            daily_data[current] = {
                "total": nb_total,
                "covered": nb_covered,
                "agents": [self.agent_repo.get(aid) for aid in agent_ids]
            }

            current += timedelta(days=1)

        return daily_data

    # --------------------------
    # Affichage
    # --------------------------

    def analyze_tranche_diversity(self):
        """
        Analyse la diversité des agents affectés par tranche sur la période.
        Pour chaque tranche :
        - Compte le nombre d'agents distincts affectés
        - Affiche les noms des agents affectés
        - Met en évidence les tranches critiques (aucune ou faible diversité)
        """
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        GRAY = "\033[90m"

        tranches = self.get_tranches()
        affectations = self.get_affectations()

        if not tranches:
            print(f"{YELLOW}[INFO]{RESET} Aucun tranche associée au poste.")
            return

        print(f"\n{BOLD}{CYAN}📈 Analyse de diversité par tranche — Poste {self.poste.nom}{RESET}")

        # Précharger les agents pour éviter les multiples appels au repo
        agent_cache = {}

        for tranche in tranches:
            # Récupérer les affectations pour cette tranche
            tranche_affectations = [aff for aff in affectations if aff.tranche_id == tranche.id]

            # Extraire les IDs uniques
            agent_ids = {aff.agent_id for aff in tranche_affectations}
            nb_agents = len(agent_ids)
            nb_affectations = len(tranche_affectations)
            total_jours = (self.end_date - self.start_date).days + 1

            # Déterminer la couleur
            if nb_agents == 0:
                color = RED
            elif nb_agents == 1:
                color = YELLOW
            else:
                color = GREEN

            # Récupérer les noms complets des agents
            agent_names = []
            for agent_id in agent_ids:
                if agent_id not in agent_cache:
                    agent = self.agent_repo.get(agent_id)
                    agent_cache[agent_id] = agent
                else:
                    agent = agent_cache[agent_id]

                if agent:
                    agent_names.append(agent.get_full_name())

            agent_names_str = ", ".join(agent_names) if agent_names else f"{GRAY}(aucun agent){RESET}"

            print(
                f"  - {tranche.abbr:<10} : {color}{nb_agents} agent(s) distinct(s){RESET} "
                f"({nb_affectations}/{total_jours} affectations) → {agent_names_str}"
            )

    def print_detailed_planning(self):
        """
        Affiche le planning du poste sous forme matricielle, avec couleurs :
        - Chaque ligne correspond à un jour
        - Chaque colonne correspond à une tranche
        - Chaque cellule affiche le nom complet de l'agent affecté (vert) ou en rouge si non couvert
        """
        RESET = "\033[0m"
        RED = "\033[91m"
        GREEN = "\033[92m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        GRAY = "\033[90m"

        tranches = self.get_tranches()
        tranche_ids = [t.id for t in tranches]
        tranche_abbrs = [t.abbr for t in tranches]

        if not tranches:
            print(f"[INFO] Aucun tranche pour le poste {self.poste.nom}")
            return

        # En-têtes avec couleur
        headers = [f"{CYAN}{BOLD}Date{RESET}"] + [f"{BOLD}{abbr}{RESET}" for abbr in tranche_abbrs]

        # Pré-chargement des affectations
        affectations = self.get_affectations()

        # Indexation rapide (jour, tranche_id) -> agent
        index = {}
        for aff in affectations:
            index[(aff.jour, aff.tranche_id)] = self.agent_repo.get(aff.agent_id)

        # Construction du tableau
        rows = []
        current = self.start_date
        while current <= self.end_date:
            row = [f"{GRAY}{current.strftime('%Y-%m-%d')}{RESET}"]
            for tid in tranche_ids:
                agent = index.get((current, tid))
                if agent:
                    cell = f"{GREEN}{agent.get_full_name()}{RESET}"
                else:
                    cell = f"{RED}{BOLD}- ABSENT -{RESET}"
                row.append(cell)
            rows.append(row)
            current += timedelta(days=1)

        # Affichage
        print(f"\n{BOLD}📅 Planning détaillé du poste {self.poste.nom}{RESET}")
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))


    def summary(self):
        """
        Affiche un résumé clair et coloré de la couverture d'un poste sur la période :
        - Nombre total de jours
        - Nombre total de tranches à couvrir
        - Nombre de tranches couvertes
        - Taux de couverture global
        - Détail par tranche (facultatif)
        """
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        GRAY = "\033[90m"

        tranches = self.get_tranches()
        tranche_ids = [t.id for t in tranches]
        nb_tranches = len(tranche_ids)

        if nb_tranches == 0:
            print(f"{YELLOW}[INFO]{RESET} Aucun tranche associée au poste {self.poste.nom}")
            return

        nb_jours = (self.end_date - self.start_date).days + 1
        total_theorique = nb_jours * nb_tranches

        # Récupérer les affectations
        affectations = self.get_affectations()

        # Tranches effectivement couvertes
        total_couvert = len(affectations)

        taux_couverture_global = (total_couvert / total_theorique) * 100 if total_theorique > 0 else 0

        print(f"\n{BOLD}{CYAN}📊 Résumé du planning poste : {self.poste.nom}{RESET}")
        print(f"  {GRAY}Période       :{RESET} {self.start_date} → {self.end_date} ({nb_jours} jours)")
        print(f"  {GRAY}Tranches/jour :{RESET} {nb_tranches}")
        print(f"  {GRAY}Total attendu :{RESET} {total_theorique}")
        print(f"  {GRAY}Total couvert :{RESET} {GREEN}{total_couvert}{RESET}")
        if taux_couverture_global < 90:
            couleur_taux = RED
        elif taux_couverture_global < 100:
            couleur_taux = YELLOW
        else:
            couleur_taux = GREEN
        print(f"  {GRAY}Taux global   :{RESET} {couleur_taux}{taux_couverture_global:.2f}%{RESET}")

        # Détail par tranche
        print(f"\n{BOLD}{CYAN}Détail par tranche :{RESET}")
        for tranche in tranches:
            total_attendu_tranche = nb_jours
            total_couvert_tranche = sum(1 for aff in affectations if aff.tranche_id == tranche.id)
            taux_tranche = (total_couvert_tranche / total_attendu_tranche) * 100 if total_attendu_tranche > 0 else 0

            if taux_tranche < 90:
                couleur = RED
            elif taux_tranche < 100:
                couleur = YELLOW
            else:
                couleur = GREEN

            print(f"  - {tranche.abbr:<10} : {couleur}{taux_tranche:6.2f}%{RESET} ({total_couvert_tranche}/{total_attendu_tranche})")
