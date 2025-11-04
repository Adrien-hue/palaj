# core/agent_planning.py
from datetime import date, datetime, time, timedelta
from typing import Iterable, Optional, List, Tuple

from core.domain.entities import Affectation, Agent, EtatJourAgent, Tranche

from core.domain.entities.work_day import WorkDay

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.poste_repo import PosteRepository
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.tranche_repo import TrancheRepository


class AgentPlanning:
    """
    Représente la vision planning d'un agent sur une période donnée.
    Les données sont récupérées via les repositories fournis (injection explicite).
    """

    def __init__(
        self,
        agent: Agent,
        start_date: date,
        end_date: date,
        affectation_repo: AffectationRepository,
        etat_jour_agent_repo: EtatJourAgentRepository,
        poste_repo: PosteRepository,
        qualification_repo: QualificationRepository,
        tranche_repo: TrancheRepository,
    ):
        self.agent = agent
        self.start_date = start_date
        self.end_date = end_date

        # Dépendances injectées
        self.affectation_repo = affectation_repo
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.poste_repo = poste_repo
        self.qualification_repo = qualification_repo
        self.tranche_repo = tranche_repo

        # Lazy-loaded
        self._affectations: Optional[List[Affectation]] = None
        self._etats: Optional[List[EtatJourAgent]] = None

        self._work_days: Optional[List[WorkDay]] = None

        self._absences_jours: Optional[List[EtatJourAgent]] = None
        self._conges_jours: Optional[List[EtatJourAgent]] = None
        self._repos_jours: Optional[List[EtatJourAgent]] = None
        self._travail_jours: Optional[List[EtatJourAgent]] = None
        self._zcot_jours: Optional[List[EtatJourAgent]] = None

        self._load_data()

    # -----------------------------
    # Méthode utilitaires
    # -----------------------------

    def _get_nb_jours(self) -> int:
        """
        Retourne le nombre de jours dans la période.
        """
        return (self.end_date - self.start_date).days + 1
    
    def _load_data(self):
        # Charger toutes les affectations et états pour la période
        self.get_affectations()
        self.get_etats()

        self._build_work_days()

        self.get_absences_jours()
        self.get_conges_jours()
        self.get_repos_jours()
        self.get_travail_jours()
        self.get_zcot_jours()

    # -----------------------------
    # Chargements des données
    # -----------------------------
    def _build_work_days(self):
        """Construit la liste des WorkDay à partir des affectations et états."""
        work_days: List[WorkDay] = []

        current = self.start_date
        while current <= self.end_date:
            if not self._etats:
                self.get_etats()

            etats = self._etats or []
            etat = next((e for e in etats if e.jour == current), None)

            if not self._affectations:
                self.get_affectations()

            affectations = self._affectations or []
            affs = [a for a in affectations if a.jour == current]

            # Résoudre les tranches correspondantes
            tranches: List[Tranche] = []
            for a in affs:
                t = self.tranche_repo.get(a.tranche_id)
                if t:
                    tranches.append(t)

            work_days.append(WorkDay(jour=current, etat=etat, tranches=tranches))
            current += timedelta(days=1)

        self._work_days = work_days

    def get_affectations(self):
        """Retourne les affectations de l'agent sur la période."""
        if self._affectations is None:
            self._affectations = [
                a for a in self.affectation_repo.list_for_agent(self.agent.id)
                if self.start_date <= a.jour <= self.end_date
            ]
        return self._affectations
    
    def get_agent(self):
        """Retourne l'agent associé à la planification."""
        return self.agent

    def get_etats(self):
        """Retourne les états de journée de l'agent sur la période."""
        if self._etats is None:
            self._etats = [
                e for e in self.etat_jour_agent_repo.list_for_agent(self.agent.id)
                if self.start_date <= e.jour <= self.end_date
            ]
        return self._etats

    def get_all_etat_jour_agent(self):
        return (
            (self._travail_jours or [])
            + (self._zcot_jours or [])
            + (self._repos_jours or [])
            + (self._absences_jours or [])
            + (self._conges_jours or [])
        )

    def get_zcot_jours(self):
        if self._zcot_jours is None:
            self._zcot_jours = [
                e for e in self.etat_jour_agent_repo.list_zcot_for_agent(self.agent.id)
                if self.start_date <= e.jour <= self.end_date
            ]
        return self._zcot_jours

    def get_repos_jours(self):
        if self._repos_jours is None:
            self._repos_jours = [
                e for e in self.etat_jour_agent_repo.list_repos_for_agent(self.agent.id)
                if self.start_date <= e.jour <= self.end_date
            ]
        return self._repos_jours

    def get_absences_jours(self):
        if self._absences_jours is None:
            self._absences_jours = [
                e for e in self.etat_jour_agent_repo.list_absences_for_agent(self.agent.id)
                if self.start_date <= e.jour <= self.end_date
            ]
        return self._absences_jours

    def get_travail_jours(self):
        if self._travail_jours is None:
            self._travail_jours = [
                e for e in self.etat_jour_agent_repo.list_travail_for_agent(self.agent.id)
                if self.start_date <= e.jour <= self.end_date
            ]
        return self._travail_jours
    
    def get_conges_jours(self):
        if self._conges_jours is None:
            self._conges_jours = [
                e for e in self.etat_jour_agent_repo.list_conges_for_agent(self.agent.id)
                if self.start_date <= e.jour <= self.end_date
            ]
        return self._conges_jours
    
    def get_end_date(self):
        """
        Retourne la date de fin de la période de planification.
        """
        return self.end_date

    def get_start_date(self):
        """
        Retourne la date de début de la période de planification.
        """
        return self.start_date

    def get_work_days(self):
        """
        Retourne la liste des jours de travail de l'agent.
        """
        return self._work_days or []

    # -----------------------------
    # Analyses des données
    # -----------------------------

    def get_all_coverage_rates(self) -> dict[str, float]:
        """
        Retourne un dictionnaire {nom_poste: taux_couverture}
        pour tous les postes sur lesquels l'agent est qualifié.
        """
        rates = {}

        # Les qualifications sont déjà chargées en mémoire via l'agent
        qualifications = self.agent.get_qualifications(self.qualification_repo)

        for q in qualifications:
            poste = q.get_poste(self.poste_repo)
            if not poste:
                print(f"[WARNING] Poste introuvable pour la qualification {q}")
                continue

            tranche_ids_poste = {t.id for t in poste.get_tranches(self.tranche_repo)}
            if not tranche_ids_poste:
                rates[poste.nom] = 0.0
                continue

            total_theorique = len(tranche_ids_poste) * self._get_nb_jours()
            if total_theorique == 0:
                rates[poste.nom] = 0.0
                continue

            # Comptage direct dans les affectations déjà chargées
            nb_couvert = sum(
                1 for aff in (self._affectations or [])
                if aff.tranche_id in tranche_ids_poste
            )

            rates[poste.nom] = round((nb_couvert / total_theorique) * 100, 1)

        return rates

    
    def get_dimanches_stats(self) -> tuple[int, int]:
        """
        Retourne (nb_dimanches_travaillés, nb_dimanches_total) sur la période.
        Un dimanche travaillé est un jour avec une affectation 'travail' ou 'ZCOT'.
        """
        nb_dimanches_total = 0
        nb_dimanches_travailles = 0

        # Index des jours travaillés
        travail_dates = {etat.jour for etat in (self._travail_jours or [])}
        zcot_dates = {etat.jour for etat in (self._zcot_jours or [])}

        current = self.start_date
        while current <= self.end_date:
            if current.weekday() == 6:  # Dimanche
                nb_dimanches_total += 1
                if current in travail_dates or current in zcot_dates:
                    nb_dimanches_travailles += 1
            current += timedelta(days=1)

        return nb_dimanches_travailles, nb_dimanches_total
    
    def get_total_heures_travaillees(self) -> float:
        """
        Calcule le total d'heures travaillées par l'agent sur la période :
        - Tranches : selon leur durée réelle
        - ZCOT : 8h fixes par jour
        """
        total_heures = 0.0

        # --- Tranches (jours de travail classiques) ---
        if self._affectations:
            for aff in self._affectations:
                if aff.tranche_id is not None:
                    tranche = self.tranche_repo.get(aff.tranche_id)
                    if tranche:
                        total_heures += tranche.duree()

        # --- ZCOT (8h fixes par jour) ---
        if self._zcot_jours:
            total_heures += len(self._zcot_jours) * 8

        return round(total_heures, 2)

    def iter_jours(self) -> Iterable[Tuple[date, List[Affectation], List[EtatJourAgent]]]:
        """
        Génère les jours de la période avec leurs données associées :
        yield (jour, tranches, etats)
        """
        affectations = self.get_affectations()
        
        etats = self.get_all_etat_jour_agent()

        # Indexer affectations par jour
        affectations_by_day = {}
        for a in affectations:
            affectations_by_day.setdefault(a.jour, []).append(a)

        etats_by_day = {}
        for e in etats:
            etats_by_day.setdefault(e.jour, []).append(e)

        jour = self.start_date
        while jour <= self.end_date:
            tranches = [a for a in affectations_by_day.get(jour, [])]
            etats_jour = etats_by_day.get(jour, [])
            yield jour, tranches, etats_jour
            jour += timedelta(days=1)
    
    # -----------------------------
    # Affichage des données
    # -----------------------------

    def print_detailed_planning(self):
        """
        Affiche le planning détaillé jour par jour pour l'agent sur la période.
        Indique : Repos / Absence / ZCOT / Tranches travaillées.
        """
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GRAY = "\033[90m"
        YELLOW = "\033[93m"
        GREEN = "\033[92m"
        RED = "\033[91m"
        BLUE = "\033[94m"

        print(f"\n{BOLD}{CYAN}📅 Planning détaillé de {self.agent.get_full_name()}{RESET}")
        print(f"Période : {self.start_date} → {self.end_date}")
        print("-" * 60)

        # Préparer des index pour lookup rapide
        travail_by_day = {}
        if self._affectations:
            for aff in self._affectations:
                travail_by_day.setdefault(aff.jour, []).append(aff.tranche_id)

        zcot_days = {etat.jour for etat in (self._zcot_jours or [])}
        repos_days = {etat.jour for etat in (self._repos_jours or [])}
        absence_days = {etat.jour for etat in (self._absences_jours or [])}
        conges_days = {etat.jour for etat in (self._conges_jours or [])}

        current = self.start_date
        while current <= self.end_date:
            jour_str = current.strftime("%a %d/%m/%Y")
            line = f"{GRAY}{jour_str}{RESET} : "

            if current in repos_days:
                line += f"{BLUE}Repos{RESET}"
            elif current in conges_days:
                line += f"{CYAN}Congés{RESET}"
            elif current in absence_days:
                line += f"{RED}Absence{RESET}"
            elif current in zcot_days:
                line += f"{YELLOW}ZCOT (8h){RESET}"
            elif current in travail_by_day:
                tranche_ids = travail_by_day[current]
                tranche_strs = []
                for tid in tranche_ids:
                    tranche = self.tranche_repo.get(tid)
                    if tranche:
                        tranche_strs.append(f"{GREEN}{tranche.abbr}{RESET}")
                    else:
                        tranche_strs.append(f"{RED}Tranche {tid} ?{RESET}")
                line += " | ".join(tranche_strs)
            else:
                line += f"{GRAY}Aucune affectation{RESET}"

            print(line)
            current += timedelta(days=1)

    def summary(self):
        """
        Affiche un résumé synthétique du planning de l'agent sur la période.
        Inclut : période, nombre d'heures, dimanches, ZCOT, absences, taux de couverture par poste.
        """
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        YELLOW = "\033[93m"
        GREEN = "\033[92m"
        GRAY = "\033[90m"
        BLUE = "\033[94m"
        RED = "\033[91m"

        # --- Calculs généraux ---
        nb_heures = self.get_total_heures_travaillees()
        nb_dim_trav, nb_dim_tot = self.get_dimanches_stats()
        nb_zcot = len(self.get_zcot_jours())
        nb_abs = len(self.get_absences_jours())
        nb_repos = len(self.get_repos_jours())
        nb_conges = len(self.get_conges_jours())

        # --- En-tête ---
        print(f"{BOLD}{CYAN}📅 Planning de {self.agent.get_full_name()} {RESET}")
        print(f"  {GRAY}Période:{RESET} {self.start_date} → {self.end_date} ({self._get_nb_jours()} jours)")
        print(f"  {GRAY}Heures travaillées:{RESET} {YELLOW}{nb_heures} h{RESET}")
        print(f"  {GRAY}Dimanches travaillés:{RESET} {GREEN}{nb_dim_trav}/{nb_dim_tot}{RESET}")
        print(f"  {GRAY}ZCOT:{RESET} {YELLOW}{nb_zcot}{RESET} | "
            f"{GRAY}Absences:{RESET} {YELLOW}{nb_abs}{RESET} | "
            f"{GRAY}Repos:{RESET} {YELLOW}{nb_repos}{RESET} | "
            f"{GRAY}Congés:{RESET} {YELLOW}{nb_conges}{RESET}")

        # --- Taux de couverture par poste ---
        coverage_rates = self.get_all_coverage_rates()
        if coverage_rates:
            print(f"\n{BOLD}{BLUE}📊 Taux de couverture par poste{RESET}")
            for poste, taux in coverage_rates.items():
                print(f"  - {poste:<20} : {GREEN}{taux:.1f}%{RESET}")
        else:
            print(f"\n{RED}Aucune qualification enregistrée pour cet agent.{RESET}")