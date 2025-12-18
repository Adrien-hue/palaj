# core/application/services/planning/repos_stats_analyzer.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Set

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.periode_repos import PeriodeRepos
from core.application.services.planning.periode_repos_analyzer import (
    PeriodeReposAnalyzer,
)
from core.domain.models.work_day import WorkDay


@dataclass
class ReposSummary:
    """Résumé agrégé des périodes de repos sur un PlanningContext."""
    periodes: List[PeriodeRepos]

    # Ensemble de tous les jours de repos (sans doublons)
    rp_days: Set[date]

    # Nb total de jours de repos (toutes périodes confondues, sans doublons)
    total_rp_days: int

    # Nb total de dimanches qui sont des jours de repos
    total_rp_sundays: int

    # Comptages de périodes
    rp_simple: int
    rp_double: int
    rp_triple: int
    rp_4plus: int

    # Comptages de qualifs week-end
    rpsd: int  # Samedi-Dimanche
    werp: int  # Sam-Dim ou Dim-Lun


class ReposStatsAnalyzer:
    """
    Service d'analyse des repos, basé sur PeriodeReposAnalyzer.

    Il encapsule la logique de comptage :
      - RP simples / doubles / triples / 4+ jours
      - RPSD (samedi-dimanche)
      - WERP (samedi-dimanche ou dimanche-lundi)
      - Total de jours de repos
      - Total de dimanches de repos
    """

    def __init__(self):
        self.periode_analyzer = PeriodeReposAnalyzer()

    def summarize_context(self, context: PlanningContext) -> ReposSummary:
        """
        Méthode historique : détecte les périodes de repos à partir
        d'un PlanningContext.

        Elle délègue simplement à detect_from_workdays pour ne pas dupliquer
        la logique.
        """
        if not context.work_days:
            return self.summarize_workdays([])

        return self.summarize_workdays(context.work_days)
        

    def summarize_workdays(self, work_days: List[WorkDay]) -> ReposSummary:
        """
        Détecte les périodes de repos sur tout le contexte
        et retourne un résumé agrégé.
        """
        periodes = self.periode_analyzer.detect_from_workdays(work_days)

        if not periodes:
            return ReposSummary(
                periodes=[],
                rp_days=set(),
                total_rp_days=0,
                total_rp_sundays=0,
                rp_simple=0,
                rp_double=0,
                rp_triple=0,
                rp_4plus=0,
                rpsd=0,
                werp=0,
            )

        # Ensemble de tous les jours de repos (pour éviter les doublons)
        rp_days: set[date] = set()
        total_sundays = 0

        rp_simple = 0
        rp_double = 0
        rp_triple = 0
        rp_4plus = 0
        rpsd = 0
        werp = 0

        for pr in periodes:
            # agrégation des jours
            for d in pr.jours:
                if d not in rp_days:
                    rp_days.add(d)
                    if d.weekday() == 6:  # dimanche
                        total_sundays += 1

            # classification de la période
            if pr.is_simple():
                rp_simple += 1
            elif pr.is_double():
                rp_double += 1
            elif pr.is_triple():
                rp_triple += 1
            elif pr.is_4plus():
                rp_4plus += 1

            # qualifs week-end
            if pr.is_rpsd():
                rpsd += 1
            if pr.is_werp():
                werp += 1

        return ReposSummary(
            periodes=periodes,
            rp_days=rp_days,
            total_rp_days=len(rp_days),
            total_rp_sundays=total_sundays,
            rp_simple=rp_simple,
            rp_double=rp_double,
            rp_triple=rp_triple,
            rp_4plus=rp_4plus,
            rpsd=rpsd,
            werp=werp,
        )