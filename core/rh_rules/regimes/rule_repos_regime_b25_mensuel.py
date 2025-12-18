# core/rh_rules/rule_repos_regime_b25_mensuel.py
from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.month_rule import MonthRule
from core.utils.domain_alert import DomainAlert, Severity
from core.application.services.planning.repos_stats_analyzer import ReposStatsAnalyzer


class RegimeB25ReposMensuelRule(MonthRule):
    """
    Règle mensuelle spécifique au régime B25 (regime_id = 1).

    Pour chaque mois civil COMPLET :
      - Au moins 1 RPSD (repos samedi-dimanche)
      - Au moins 1 autre repos de 2 jours ou plus
        → au total : au moins 2 périodes de RP de ≥ 2 jours, dont ≥1 RPSD.

    Pour les mois partiels :
      - suivi informatif uniquement (si au moins un RP dans le mois)
    """

    name = "RegimeB25ReposMensuelRule"
    description = (
        "Contrôle mensuel des repos B25 : par mois complet, au moins 1 RPSD et "
        "au moins 2 périodes de repos de 2+ jours (dont ≥1 RPSD)."
    )

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

    # On court-circuite ici pour éviter de lancer MonthRule sur les autres régimes
    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        if not self.applies_to(context):
            return True, []
        if not context.work_days:
            return True, []
        return super().check(context)

    # ---------------------------------------------------------
    # Implémentation métier pour un mois
    # ---------------------------------------------------------
    def check_month(
        self,
        context: PlanningContext,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        # Aucun jour pour ce mois → rien à signaler
        if not work_days:
            return True, alerts

        label = f"{year}-{month:02d}"

        # Statistiques de repos à partir des work_days de ce mois
        repos_summary = self.analyzer.summarize_workdays(work_days)
        nb_rp_month = repos_summary.total_rp_days

        # Mois partiel → suivi INFO uniquement
        if not is_full:
            if nb_rp_month > 0:
                alerts.append(
                    self.info(
                        msg=(
                            f"[{label}] Régime B25 - Suivi mensuel (mois partiel) : "
                            f"{nb_rp_month} jour(s) de repos."
                        ),
                        code="B25_MOIS_PARTIEL",
                    )
                )
            return True, alerts

        # Mois complet → contrôle strict B25 :
        #   - au moins 1 RPSD
        #   - au moins 2 périodes de repos de 2+ jours (dont ≥ 1 RPSD)
        rpsd_count = 0
        rp_2plus_count = 0

        for pr in repos_summary.periodes:
            # On range la période dans un mois via sa date de début
            if not (month_start <= pr.start <= month_end):
                continue

            if pr.nb_jours >= 2:
                rp_2plus_count += 1
            if pr.is_rpsd():
                rpsd_count += 1

        # Résumé systématique
        alerts.append(
            self.info(
                msg=(
                    f"[{label}] Régime B25 - Repos mensuels : "
                    f"RPSD={rpsd_count}, périodes de 2+ jours={rp_2plus_count}."
                ),
                code="B25_MOIS_SYNTHESIS",
            )
        )

        # Contrôle des seuils
        if rpsd_count < 1 or rp_2plus_count < 2:
            alerts.append(
                self.error(
                    msg=(
                        f"[{label}] Régime B25 - Repos mensuels insuffisants : "
                        f"RPSD={rpsd_count} (min 1), "
                        f"RP doubles/2+={rp_2plus_count} (min 2)."
                    ),
                    code="B25_MOIS_NON_CONFORME",
                )
            )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
