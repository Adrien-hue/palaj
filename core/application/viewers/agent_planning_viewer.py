# core/application/viewers/agent_planning_viewer.py

from datetime import timedelta
from core.domain.models.agent_planning import AgentPlanning
from core.domain.entities import TypeJour

class AgentPlanningViewer:
    """
    Affichage console du planning d'un agent sur une période donnée.
    Fonctionne uniquement à partir d'un AgentPlanning .
    """

    # Couleurs ANSI
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"

    def print_detailed(self, planning):
        """
        Affiche un planning détaillé jour par jour :
        - Repos, Absence, Congé, ZCOT, Tranches travaillées
        """

        print(f"\n{self.BOLD}{self.CYAN}Planning détaillé de {planning.agent.get_full_name()}{self.RESET}")
        print(f"Période : {planning.start_date} → {planning.end_date}")
        print("-" * 60)

        # Index jour → liste de tranches
        travail_by_day = {
            wd.jour: [t.nom for t in wd.tranches]
            for wd in planning.work_days
            if wd.is_working()
        }

        # Index jour → type de jour
        type_by_day = {
            wd.jour: wd.type()
            for wd in planning.work_days
        }

        current = planning.start_date
        while current <= planning.end_date:
            wd_type = type_by_day.get(current, None)

            jour_str = current.strftime("%a %d/%m/%Y")
            line = f"{self.GRAY}{jour_str}{self.RESET} : "

            if wd_type == TypeJour.REPOS:
                line += f"{self.BLUE}Repos{self.RESET}"

            elif wd_type == TypeJour.CONGE:
                line += f"{self.CYAN}Congés{self.RESET}"

            elif wd_type == TypeJour.ABSENCE:
                line += f"{self.RED}Absence{self.RESET}"

            elif wd_type == TypeJour.ZCOT:
                line += f"{self.YELLOW}ZCOT (8h){self.RESET}"

            elif wd_type == TypeJour.POSTE:
                tranches = travail_by_day.get(current, [])
                if tranches:
                    line += " | ".join(f"{self.GREEN}{t}{self.RESET}" for t in tranches)
                else:
                    line += f"{self.RED}POSTE mais aucune tranche ?!{self.RESET}"

            else:
                line += f"{self.GRAY}Aucune information{self.RESET}"

            print(line)
            current += timedelta(days=1)

    def summary(self, planning: AgentPlanning):
        """
        Affiche un résumé synthétique du planning de l'agent sur la période.
        Inclut :
        - période
        - heures travaillées
        - dimanches
        - ZCOT / absences / repos / congés
        - taux de couverture par poste
        """

        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        YELLOW = "\033[93m"
        GREEN = "\033[92m"
        GRAY = "\033[90m"
        BLUE = "\033[94m"
        RED = "\033[91m"

        # --- 1) Calculs généraux ---
        nb_jours = planning.get_nb_jours()
        nb_heures = planning.get_total_heures_travaillees()
        nb_dim_trav, nb_dim_tot = planning.get_dimanches_stats()

        nb_zcot = len(planning.get_zcot_jours())
        nb_abs = len(planning.get_absences_jours())
        nb_repos = len(planning.get_repos_jours())
        nb_conges = len(planning.get_conges_jours())

        # --- 2) En-tête ---
        print(f"{BOLD}{CYAN}Planning de {planning.agent.get_full_name()}{RESET}")
        print(f"  {GRAY}Période :{RESET} {planning.start_date} → {planning.end_date} ({nb_jours} jours)")
        print(f"  {GRAY}Heures travaillées :{RESET} {YELLOW}{nb_heures} h{RESET}")
        print(f"  {GRAY}Dimanches travaillés :{RESET} {GREEN}{nb_dim_trav}/{nb_dim_tot}{RESET}")
        print(
            f"  {GRAY}ZCOT:{RESET} {YELLOW}{nb_zcot}{RESET} | "
            f"{GRAY}Absences:{RESET} {YELLOW}{nb_abs}{RESET} | "
            f"{GRAY}Repos:{RESET} {YELLOW}{nb_repos}{RESET} | "
            f"{GRAY}Congés:{RESET} {YELLOW}{nb_conges}{RESET}"
        )