# core/multi_poste_planning.py
from datetime import date, timedelta
from typing import Counter, List
from tabulate import tabulate

from core.domain.entities import Poste
from core.poste_planning import PostePlanning


class MultiPostePlanning:
    """
    Vue consolidée de plusieurs plannings de poste sur une période donnée.
    Permet d'analyser la couverture globale et d'afficher une matrice multi-postes.
    """
    def __init__(
        self, 
        postes: List[Poste], 
        start_date: date, 
        end_date: date,
        affectation_repo,
        tranche_repo,
        agent_repo
    ):
        self.postes = postes
        self.start_date = start_date
        self.end_date = end_date

        self.affectation_repo = affectation_repo
        self.tranche_repo = tranche_repo
        self.agent_repo = agent_repo

        # Génération d'un PostePlanning pour chaque poste
        self._poste_plannings: List[PostePlanning] = [
            PostePlanning(
                poste=poste,
                start_date=start_date,
                end_date=end_date,
                affectation_repo=affectation_repo,
                tranche_repo=tranche_repo,
                agent_repo=agent_repo
            )
            for poste in postes
        ]
    
    def analyze_hotspots(self, top_n: int = 5):
        """
        Analyse les jours et tranches les plus problématiques (non couverts).
        - top_n : nombre d'entrées à afficher pour chaque catégorie.
        """
        # --- Couleurs ---
        RESET = "\033[0m"
        BOLD = "\033[1m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        GRAY = "\033[90m"

        uncovered_by_day = Counter()
        uncovered_by_tranche = Counter()

        # Collecte des infos depuis chaque PostePlanning
        for poste_planning in self._poste_plannings:
            uncovered = poste_planning.find_uncovered_shifts()
            for jour, tranche in uncovered:
                uncovered_by_day[jour] += 1
                uncovered_by_tranche[tranche.abbr] += 1

        jours_critiques = uncovered_by_day.most_common(top_n)
        tranches_critiques = uncovered_by_tranche.most_common(top_n)

        # --- Affichage ---
        print(f"\n{BOLD}{CYAN}🔥 Analyse des Points Chauds{RESET}")

        print(f"\n{BOLD}📅 Jours les plus problématiques :{RESET}")
        if not jours_critiques:
            print(f"  {GRAY}✅ Aucun jour problématique détecté{RESET}")
        else:
            for jour, count in jours_critiques:
                color = RED if count >= 3 else YELLOW if count >= 1 else GRAY
                print(f"  - {color}{jour}{RESET} : {BOLD}{count}{RESET} tranches non couvertes")

        print(f"\n{BOLD}🧭 Tranches les plus problématiques :{RESET}")
        if not tranches_critiques:
            print(f"  {GRAY}✅ Aucune tranche problématique détectée{RESET}")
        else:
            for tranche_abbr, count in tranches_critiques:
                color = RED if count >= 3 else YELLOW if count >= 1 else GRAY
                print(f"  - {color}{tranche_abbr}{RESET} : {BOLD}{count}{RESET} jours non couverts")

    # ---------- AFFICHAGE ----------

    def print_global_matrix(self):
        """
        Matrice multi-postes :
          - Lignes = jours
          - Colonnes = Poste-Tranche
          - Cellule = nom complet (vert), '❌' (rouge) si non couvert,
                      'A / B' (jaune) si plusieurs affectations sur le même créneau.
        """
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        GRAY = "\033[90m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        # Colonnes dynamiques
        colonne_specs = []  # [(poste_planning, tranche)]
        headers = [f"{CYAN}{BOLD}Date{RESET}"]
        for pp in self._poste_plannings:
            tranches = pp.get_tranches()
            for t in tranches:
                colonne_specs.append((pp, t))
                headers.append(f"{BOLD}{pp.poste.nom} - {t.abbr}{RESET}")

        rows = []
        d = self.start_date
        while d <= self.end_date:
            row = [f"{GRAY}{d.strftime('%Y-%m-%d')}{RESET}"]
            for pp, tranche in colonne_specs:
                affs = [a for a in pp.get_affectations_for_day(d) if a.tranche_id == tranche.id]
                if not affs:
                    cell = f"{RED}ABSENT{RESET}"
                elif len(affs) == 1:
                    ag = self.agent_repo.get(affs[0].agent_id)
                    cell = f"{GREEN}{ag.get_full_name() if ag else '???'}{RESET}"
                else:
                    # Plusieurs affectations sur le même créneau → on liste
                    names = []
                    for a in affs:
                        ag = self.agent_repo.get(a.agent_id)
                        names.append(ag.get_full_name() if ag else "???")
                    cell = f"{YELLOW}{' / '.join(names)}{RESET}"
                row.append(cell)
            rows.append(row)
            d += timedelta(days=1)

        print(f"\n{BOLD}📅 Vue multi-postes {self.start_date} → {self.end_date}{RESET}")
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))

    def summary(self):
        """
        Résumé global multi-postes : couverture globale et détail par poste.
        """
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        
        total_slots = 0
        total_uncovered = 0
        details = []

        nb_days = (self.end_date - self.start_date).days + 1

        for pp in self._poste_plannings:
            tranches = pp.get_tranches()
            nb_tranches = len(tranches)
            slots_poste = nb_tranches * nb_days
            uncovered_poste = len(pp.find_uncovered_shifts())

            total_slots += slots_poste
            total_uncovered += uncovered_poste

            coverage = (1 - uncovered_poste / slots_poste) * 100 if slots_poste else 0.0
            details.append((pp.poste.nom, coverage, uncovered_poste, slots_poste))

        global_coverage = (1 - total_uncovered / total_slots) * 100 if total_slots else 0.0

        print(f"\n{BOLD}📊 Résumé Multi-Postes{RESET}")
        print(f"  Période : {self.start_date} → {self.end_date}")
        print(f"  Postes analysés : {len(self._poste_plannings)}")
        print(f"  Couverture globale : {GREEN if global_coverage==100 else YELLOW if global_coverage>=90 else RED}"
              f"{global_coverage:.1f}%{RESET} ({total_slots - total_uncovered}/{total_slots} créneaux couverts)")

        print("\n  Détail par poste :")
        for nom, cov, uncov, slots in details:
            color = GREEN if cov == 100 else YELLOW if cov >= 90 else RED
            print(f"   - {nom:<18} : {color}{cov:6.2f}%{RESET}  "
                  f"({slots - uncov}/{slots} couverts, {uncov} non couverts)")


    # ---------- HELPERS ----------

    def find_uncovered_slots(self):
        """Retourne une liste (date, poste, tranche) de tous les créneaux non couverts."""
        uncovered = []
        for pp in self._poste_plannings:
            uncovered.extend(pp.find_uncovered_shifts())
        return uncovered
