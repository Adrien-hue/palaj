# core/domain/contexts/planning_context.py
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

from core.domain.entities import Agent

from core.domain.models.work_day import WorkDay

from core.domain.models.agent_planning import AgentPlanning

@dataclass
class PlanningContext:
    """
    📘 PlanningContext
    ==================
    Structure métier centrale représentant le **contexte complet de planification**
    d'un agent sur une période donnée.

    Elle contient :
    - un agent (`Agent`)
    - une liste de WorkDay (jours avec états et horaires)
    - une éventuelle date de référence (début d'analyse)

    👉 Ce n'est pas un service applicatif.
    👉 C'est une *structure d'analyse métier* utilisée par les services :
       - GrandePeriodeTravailAnalyzer
       - PeriodeReposAnalyzer
       - règles RH futures
       - validations de plannings

    Toutes ses méthodes :
    - sont **pures** (aucun accès à la DB)
    - analysent les `WorkDay` déjà présents
    - ne modifient aucune donnée métier
    """

    agent: Agent
    work_days: List[WorkDay]
    date_reference: Optional[date] = None
    current_work_day: Optional[WorkDay] = None

    @property
    def start_date(self) -> Optional[date]:
        """Retourne la première date connue du contexte."""
        if not self.work_days:
            return None
        return min(wd.jour for wd in self.work_days)

    @property
    def end_date(self) -> Optional[date]:
        """Retourne la dernière date connue du contexte."""
        if not self.work_days:
            return None
        return max(wd.jour for wd in self.work_days)

    @classmethod
    def from_planning(cls, planning: AgentPlanning) -> "PlanningContext":
        """
        Construit un PlanningContext à partir d'un objet AgentPlanning.
        (Seule dépendance autorisée, car AgentPlanning est déjà métier.)
        """
        agent = planning.get_agent()
        work_days = planning.get_work_days()
        date_reference = planning.get_start_date()

        return cls(
            agent=agent,
            work_days=work_days,
            date_reference=date_reference
        )
    
    def set_current_work_day(self, work_day: Optional[WorkDay]):
        """Définit le WorkDay de référence courant."""
        self.current_work_day = work_day

    def set_date_reference(self, date_ref: Optional[date]):
        """Définit la date de référence pour le contexte de planification."""
        self.date_reference = date_ref


    def get_work_day(self, jour: date) -> Optional[WorkDay]:
        """Retourne le WorkDay correspondant à une date donnée."""
        return next((wd for wd in self.work_days if wd.jour == jour), None)

    # =============================
    # == Accès aux jours travaillés
    # =============================
    def get_previous_working_day(self, jour: date) -> Optional[WorkDay]:
        """Retourne le dernier jour travaillé avant une date donnée."""
        before = [wd for wd in self.work_days if wd.jour < jour and wd.is_working()]
        return max(before, key=lambda wd: wd.jour, default=None)

    def get_next_working_day(self, jour: date) -> Optional[WorkDay]:
        """Retourne le prochain jour travaillé après une date donnée."""
        after = [wd for wd in self.work_days if wd.jour > jour and wd.is_working()]
        return min(after, key=lambda wd: wd.jour, default=None)

    def get_all_working_days(self) -> List[WorkDay]:
        """Retourne toutes les journées travaillées."""
        return [wd for wd in self.work_days if wd.is_working()]
    

    # ===============================================
    # == Accès à la durée entre deux jours travaillés
    # ===============================================
    def get_last_working_day_gap(self, jour: date) -> Optional[int]:
        """Retourne le nombre de jours depuis la dernière journée travaillée."""
        prev = self.get_previous_working_day(jour)
        if prev:
            return (jour - prev.jour).days
        return None

    def get_next_working_day_gap(self, jour: date) -> Optional[int]:
        """Retourne le nombre de jours avant la prochaine journée travaillée."""
        nxt = self.get_next_working_day(jour)
        if nxt:
            return (nxt.jour - jour).days
        return None
    
    def get_repos_minutes_since_last_work_day(self, jour: date) -> Optional[int]:
        """Retourne la durée de repos (en minutes) entre le dernier jour travaillé et le jour donné."""
        wd_prev = self.get_previous_working_day(jour)
        wd_curr = self.get_work_day(jour)
        if not (wd_prev and wd_curr):
            return None

        end_prev = wd_prev.end_time()
        start_prev = wd_prev.start_time()
        start_curr = wd_curr.start_time()
        if not (end_prev and start_prev and start_curr):
            return None

        # 👉 Détecte si la journée précédente dépasse minuit
        # Exemple : début = 22:00, fin = 06:20 → fin réelle = lendemain
        if end_prev < start_prev:
            dt_prev = datetime.combine(wd_prev.jour + timedelta(days=1), end_prev)
        else:
            dt_prev = datetime.combine(wd_prev.jour, end_prev)

        dt_curr = datetime.combine(jour, start_curr)

        # Si la date du jour est avant la fin du service précédent → ajoute 1 jour
        if dt_curr < dt_prev:
            dt_curr += timedelta(days=1)

        return int((dt_curr - dt_prev).total_seconds() / 60)


    
    # ===========================================================================
    # == Accès à l'amplitude d'une journée et à la durée travaillé sur la période
    # ===========================================================================
    def get_amplitude_for_day(self, jour: date) -> int:
        wd = self.get_work_day(jour)
        return wd.amplitude_minutes() if wd else 0

    def get_total_hours_for_period(self) -> float:
        """Retourne le total d'heures travaillées sur toute la période."""
        return sum(wd.duree_minutes() for wd in self.work_days if wd.is_working()) / 60

    # ===========================================================================
    # == Accès à la liste de GPTs sur une période
    # ===========================================================================
    def get_gpt_segments(self) -> List[List[WorkDay]]:
        """
        Retourne la liste des GPT (grandes périodes de travail),
        c'est-à-dire des séquences consécutives de jours travaillés.
        """
        gpts = []
        current = []

        sorted_days = sorted(self.work_days, key=lambda w: w.jour)

        for wd in sorted_days:
            if wd.is_working():
                if not current or (wd.jour - current[-1].jour).days == 1:
                    current.append(wd)
                else:
                    gpts.append(current)
                    current = [wd]
            else:
                if current:
                    gpts.append(current)
                    current = []

        if current:
            gpts.append(current)

        return gpts