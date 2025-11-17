# core/domain/models/agent_planning.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, Tuple

from core.domain.entities import Agent, Affectation, EtatJourAgent, Tranche, TypeJour
from core.domain.models.work_day import WorkDay


@dataclass
class AgentPlanning:
    """
    Modèle de domaine : une vision complète du planning d'un agent
    sur une période donnée. Ne dépend d'aucun repository.
    """

    agent: Agent
    start_date: date
    end_date: date

    etats: List[EtatJourAgent]
    affectations: List[Affectation]
    tranches: List[Tranche]  # optionnel : si tu veux accélérer WorkDay

    work_days: List[WorkDay]

    @classmethod
    def build(cls,
              agent: Agent,
              start_date: date,
              end_date: date,
              etats: List[EtatJourAgent],
              affectations: List[Affectation],
              tranches_by_id: dict[int, Tranche]
    ) -> "AgentPlanning":

        work_days: List[WorkDay] = []

        current = start_date
        while current <= end_date:

            etat = next((e for e in etats if e.jour == current), None)

            affs = [a for a in affectations if a.jour == current]
            trs = [tranches_by_id[a.tranche_id]
                   for a in affs if a.tranche_id in tranches_by_id]

            work_days.append(
                WorkDay(jour=current, etat=etat, tranches=trs)
            )

            current += timedelta(days=1)

        return cls(
            agent=agent,
            start_date=start_date,
            end_date=end_date,
            etats=etats,
            affectations=affectations,
            tranches=list(tranches_by_id.values()),
            work_days=work_days,
        )

    def get_agent(self) -> Agent:
        return self.agent

    def get_start_date(self) -> date:
        return self.start_date

    def get_end_date(self) -> date:
        return self.end_date
    
    def get_nb_jours(self) -> int:
        return (self.get_end_date() - self.get_start_date()).days + 1

    def get_work_days(self) -> List[WorkDay]:
        return self.work_days
    
    def get_repos_jours(self) -> List[EtatJourAgent]:
        return [e for e in self.etats if e.type_jour == TypeJour.REPOS]

    def get_conges_jours(self) -> List[EtatJourAgent]:
        return [e for e in self.etats if e.type_jour == TypeJour.CONGE]

    def get_absences_jours(self) -> List[EtatJourAgent]:
        return [e for e in self.etats if e.type_jour == TypeJour.ABSENCE]

    def get_zcot_jours(self) -> List[EtatJourAgent]:
        return [e for e in self.etats if e.type_jour == TypeJour.ZCOT]

    def get_travail_jours(self) -> List[EtatJourAgent]:
        return [e for e in self.etats if e.type_jour == TypeJour.POSTE]

    def get_all_etats(self) -> List[EtatJourAgent]:
        return self.etats

    def get_dimanches_stats(self) -> Tuple[int, int]:
        """
        Retourne (nb_dimanches_travaillés, nb_dimanches_total).
        """
        travail_dates = {e.jour for e in self.get_travail_jours()}
        zcot_dates = {e.jour for e in self.get_zcot_jours()}

        nb_dim_total = 0
        nb_dim_trav = 0

        current = self.start_date
        while current <= self.end_date:
            if current.weekday() == 6:  # dimanche
                nb_dim_total += 1
                if current in travail_dates or current in zcot_dates:
                    nb_dim_trav += 1
            current += timedelta(days=1)

        return nb_dim_trav, nb_dim_total
    
    def get_total_heures_travaillees(self) -> float:
        """
        Heures travaillées = tranches + 8h pour ZCOT.
        """
        total_min = 0

        # tranches
        for aff in self.affectations:
            for t in self.tranches:
                if t.id == aff.tranche_id:
                    total_min += t.duree_minutes()

        # zcot
        total_min += len(self.get_zcot_jours()) * 8 * 60

        return round(total_min / 60, 2)

    def iter_days(self):
        for wd in self.work_days:
            yield wd
