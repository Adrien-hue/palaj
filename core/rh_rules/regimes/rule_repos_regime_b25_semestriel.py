# core/rh_rules/rule_repos_regime_b25_semestriel.py
from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.semester_rule import SemesterRule
from core.utils.domain_alert import DomainAlert, Severity
from core.application.services.planning.repos_stats_analyzer import ReposStatsAnalyzer


class RegimeB25ReposSemestrielRule(SemesterRule):
    """
    Règle semestrielle spécifique au régime B25 (regime_id = 1).

    Exigence (par semestre civil complet) :
    - Au moins 56 jours de repos périodiques (RP) par semestre :
      - S1 : 01/01 → 30/06
      - S2 : 01/07 → 31/12
    """

    name = "RegimeB25ReposSemestrielRule"
    description = "Repos semestriels spécifiques au régime B25 (≥ 56 RP par semestre)."

    MIN_RP_SEMESTRE = 56

    def __init__(self, analyzer: ReposStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or ReposStatsAnalyzer()

    # ---------------------------------------------------------
    # Applicabilité de la règle
    # ---------------------------------------------------------
    def applies_to(self, context: PlanningContext) -> bool:
        """
        La règle ne s'applique qu'aux agents de régime B25 (regime_id = 1).
        """
        regime_id = getattr(context.agent, "regime_id", None)
        return regime_id == 1

    # On garde le check() de SemesterRule mais on court-circuite
    # si l'agent n'est pas B25.
    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        if not self.applies_to(context):
            return True, []
        return super().check(context)

    # ---------------------------------------------------------
    # Implémentation métier pour un semestre
    # ---------------------------------------------------------
    def check_semester(
        self,
        context: PlanningContext,
        year: int,
        label: str,          # "S1" ou "S2"
        sem_start: date,
        sem_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        # Aucun jour sur ce semestre → info et c'est tout
        if not work_days:
            alerts.append(
                self.info(
                    msg=f"[{year} {label}] Aucun jour planifié sur ce semestre pour l'agent B25.",
                    code="B25_SEMESTRE_VIDE",
                )
            )
            return True, alerts

        # Statistiques de repos uniquement sur les WorkDay de ce semestre
        repos_summary = self.analyzer.summarize_workdays(work_days)

        nb_rp_sem = repos_summary.total_rp_days

        # Résumé systématique
        alerts.append(
            self.info(
                msg=(
                    f"[{year} {label}] Régime B25 - Repos périodiques sur le semestre "
                    f"{sem_start} → {sem_end} : {nb_rp_sem} RP "
                    f"(minimum attendu : {self.MIN_RP_SEMESTRE})."
                ),
                code="B25_SEMESTRE_SYNTHESIS",
            )
        )

        # Semestre partiel → suivi seulement
        if not is_full:
            alerts.append(
                self.info(
                    msg=(
                        f"[{year} {label}] Semestre partiellement couvert : "
                        "les minima semestriels B25 ne sont pas contrôlés strictement."
                    ),
                    code="B25_SEMESTRE_PARTIEL",
                )
            )
            return True, alerts

        # Semestre complet → contrôle strict
        if nb_rp_sem < self.MIN_RP_SEMESTRE:
            alerts.append(
                self.error(
                    msg=(
                        f"[{year} {label}] Repos périodiques insuffisants pour le régime B25 "
                        f"sur le semestre {sem_start} → {sem_end} : "
                        f"{nb_rp_sem}/{self.MIN_RP_SEMESTRE} jours."
                    ),
                    code="B25_SEMESTRE_RP_INSUFFISANTS",
                )
            )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
