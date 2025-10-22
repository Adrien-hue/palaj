from datetime import date, datetime, time, timedelta
from typing import Optional, List

from models.agent import Agent
from models.affectation import Affectation
from models.etat_jour_agent import EtatJourAgent
from models.tranche import Tranche

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

        self.get_absences_jours()
        self.get_conges_jours()
        self.get_repos_jours()
        self.get_travail_jours()
        self.get_zcot_jours()

    # -----------------------------
    # Chargements des données
    # -----------------------------
    def get_affectations(self):
        """Retourne les affectations de l'agent sur la période."""
        if self._affectations is None:
            self._affectations = [
                a for a in self.affectation_repo.list_for_agent(self.agent.id)
                if self.start_date <= a.jour <= self.end_date
            ]
        return self._affectations

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

    # -----------------------------
    # Analyses des données
    # -----------------------------
    def check_consistency(self) -> List[str]:
        """
        Vérifie la cohérence du planning de l'agent et retourne une liste d'alertes.
        Chaque alerte est une chaîne décrivant un problème détecté.
        """
        alerts: List[str] = []

        jour_affectations = self._index_jours()

        alerts += self._check_multi_tranches(jour_affectations)
        alerts += self._check_state_conflicts(jour_affectations)
        alerts += self._check_duplicate_states(jour_affectations)

        alerts += self._check_daily_time_constraints(jour_affectations)

        return alerts
    
    def _index_jours(self) -> dict:
        """
        Construit un dictionnaire {jour: {"etat": [], "tranches": []}}
        - "etat" : liste d'objets EtatJourAgent (repos, zcot, congé, absence)
        - "tranches" : liste d'affectations (Affectation)
        """
        jour_affectations = {}

        # Affectations (tranches de travail)
        for aff in self.get_affectations():
            jour_affectations.setdefault(aff.jour, {"etat": [], "tranches": []})
            jour_affectations[aff.jour]["tranches"].append(aff)

        # États journaliers (repos, zcot, congé, absence)
        for etat in (
            (self._zcot_jours or [])
            + (self._repos_jours or [])
            + (self._absences_jours or [])
            + (self._conges_jours or [])
        ):
            jour_affectations.setdefault(etat.jour, {"etat": [], "tranches": []})
            jour_affectations[etat.jour]["etat"].append(etat)

        return jour_affectations
    
    def _check_multi_tranches(self, jour_affectations: dict) -> List[str]:
        """Détecte les jours où un agent est affecté à plusieurs tranches."""
        alerts = []
        for jour, contenu in jour_affectations.items():
            tranches = contenu["tranches"]
            if len(tranches) > 1:
                tranche_ids = [str(t.tranche_id) for t in tranches]
                alerts.append(
                    f"[{jour}] ⚠️ Agent affecté à plusieurs tranches ({', '.join(tranche_ids)})"
                )
        return alerts

    def _check_state_conflicts(self, jour_affectations: dict) -> List[str]:
        """Détecte les incohérences entre tranches (travail) et états journaliers."""
        alerts = []
        for jour, contenu in jour_affectations.items():
            tranches, etats = contenu["tranches"], contenu["etat"]

            if not etats:
                continue

            etat_types = {e.type_jour for e in etats}
            # Si l'agent est censé être absent ou en repos mais a une tranche
            if tranches and any(e.type_jour in ("repos", "conge", "absence", "zcot") for e in etats):
                alerts.append(
                    f"[{jour}] ⚠️ Incohérence : agent affecté à une tranche alors qu’il est en {', '.join(etat_types)}"
                )
        return alerts
    
    def _check_duplicate_states(self, jour_affectations: dict) -> List[str]:
        """Détecte plusieurs états différents pour un même jour."""
        alerts = []
        for jour, contenu in jour_affectations.items():
            etats = contenu["etat"]
            if len(etats) > 1:
                types = {e.type_jour for e in etats}
                alerts.append(f"[{jour}] ⚠️ Plusieurs états détectés pour le même jour ({', '.join(types)})")
        return alerts
    
    def _check_daily_time_constraints(self, jour_affectations: dict) -> List[str]:
        """
        Vérifie les contraintes horaires structurelles :
        - amplitude max 11h
        - durée min 5h30
        - durée max 10h (ou 8h30 si travail de nuit)
        """
        alerts = []
        for jour, contenu in jour_affectations.items():
            tranches = [a.get_tranche(self.tranche_repo) for a in contenu["tranches"]]
            if not tranches:
                continue

            debut = min(t.debut for t in tranches)
            fin = max(t.fin for t in tranches)
            amplitude = self._calculer_amplitude(debut, fin)
            duree_travail = sum(t.duree() for t in tranches)
            duree_nuit = self._duree_nuit(tranches)
            duree_max = 8.5 if duree_nuit > 2.5 else 10.0

            if amplitude > 11:
                alerts.append(f"[{jour}] ⛔ Amplitude {amplitude:.1f}h > 11h")
            if duree_travail < 5.5:
                alerts.append(f"[{jour}] ⚠️ Durée de travail trop faible ({duree_travail:.1f}h)")
            if duree_travail > duree_max:
                alerts.append(f"[{jour}] ⛔ Durée de travail excessive ({duree_travail:.1f}h > {duree_max}h)")

        return alerts
    
    def _calculer_amplitude(self, debut, fin) -> float:
        debut_dt = datetime.combine(datetime.today(), debut)
        fin_dt = datetime.combine(datetime.today(), fin)
        if fin_dt < debut_dt:
            fin_dt += timedelta(days=1)
        return round((fin_dt - debut_dt).total_seconds() / 3600, 2)


    def _duree_nuit(self, tranches) -> float:
        debut_nuit, fin_nuit = time(21, 30), time(6, 30)
        total = 0.0
        for t in tranches:
            total += self._chevauchement_nuit(t.debut, t.fin, debut_nuit, fin_nuit)
        return total


    def _chevauchement_nuit(self, debut, fin, nuit_debut, nuit_fin) -> float:
        d = datetime.combine(datetime.today(), debut)
        f = datetime.combine(datetime.today(), fin)
        if f < d:
            f += timedelta(days=1)
        n1 = datetime.combine(datetime.today(), nuit_debut)
        n2 = datetime.combine(datetime.today(), nuit_fin)
        if n2 < n1:
            n2 += timedelta(days=1)
        overlap_start = max(d, n1)
        overlap_end = min(f, n2)
        return max(0.0, (overlap_end - overlap_start).total_seconds() / 3600)

    def __check_consistency(self) -> list[str]:
        """
        Vérifie la cohérence du planning de l'agent et retourne une liste d'alertes.
        Chaque alerte est une chaîne décrivant le problème détecté.
        """
        alerts = []

        # Indexer les jours avec ce qui a été planifié
        jour_affectations = {}
        for aff in self.get_affectations():
            jour_affectations.setdefault(aff.jour, {"tranches": [], "zcot": [], "etat": []})
            jour_affectations[aff.jour]["tranches"].append(aff)

        for etat in (self._zcot_jours or []) + (self._repos_jours or []) + (self._absences_jours or []) + (self._conges_jours or []):
            jour_affectations.setdefault(etat.jour, {"tranches": [], "zcot": [], "etat": []})
            if etat.type_jour == "zcot":
                jour_affectations[etat.jour]["zcot"].append(etat)
            else:
                jour_affectations[etat.jour]["etat"].append(etat)

        # print(jour_affectations)
        # exit()

        # Vérifications
        for jour, contenu in sorted(jour_affectations.items()):
            tranches = contenu["tranches"]
            zcots = contenu["zcot"]
            etats = contenu["etat"]

            # 1️⃣ Agent affecté à plusieurs tranches le même jour
            if len(tranches) > 1:
                tranche_ids = [str(t.tranche_id) for t in tranches]
                alerts.append(
                    f"[{jour}] ⚠️ Agent affecté à plusieurs tranches ({', '.join(tranche_ids)})"
                )

            # 2️⃣ Agent à la fois sur une tranche et en ZCOT
            if tranches and zcots:
                alerts.append(
                    f"[{jour}] ⚠️ Agent affecté sur tranche(s) ET en ZCOT le même jour"
                )

            # 3️⃣ Agent sur une tranche ou ZCOT alors qu’il est en absence/repos/congé
            if etats:
                etat_types = {e.type_jour for e in etats}
                if tranches or zcots:
                    alerts.append(
                        f"[{jour}] ⚠️ Incohérence : tranche/ZCOT planifié alors que le jour est marqué comme {', '.join(etat_types)}"
                    )

            # 4️⃣ Agent en ZCOT et dans plusieurs états spéciaux le même jour (théoriquement impossible)
            if len(zcots) > 1:
                alerts.append(
                    f"[{jour}] ⚠️ Plusieurs entrées ZCOT détectées pour le même jour"
                )

            if len(etats) > 1:
                alerts.append(
                    f"[{jour}] ⚠️ Plusieurs états spéciaux détectés pour le même jour ({', '.join(e.type for e in etats)})"
                )

        return alerts


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


    def has_double_affectation(self) -> List[date]:
        """
        Vérifie s'il existe des jours où l'agent a plus d'une affectation (ex : travail + ZCOT).
        Retourne la liste des dates concernées.
        """
        dates = {}

        for aff in self.get_affectations():
            dates.setdefault(aff.jour, []).append("TRAVAIL")

        for e in self.get_zcot_jours():
            dates.setdefault(e.jour, []).append("ZCOT")

        for e in self.get_absences_jours():
            dates.setdefault(e.jour, []).append("ABSENCE")

        for e in self.get_repos_jours():
            dates.setdefault(e.jour, []).append("REPOS")

        for e in self.get_conges_jours():
            dates.setdefault(e.jour, []).append("CONGE")

        return [d for d, types in dates.items() if len(types) > 1]
    
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

        errors = self.check_consistency()
        if errors:
            print(f"\n{RED}🚨 Erreurs de planification détectées :{RESET}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"\n{GREEN}✅ Aucune erreur de planification détectée.{RESET}")