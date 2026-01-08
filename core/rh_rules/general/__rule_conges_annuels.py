from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour
from core.domain.models.work_day import WorkDay
from core.rh_rules.year_rule import YearRule
from core.utils.domain_alert import DomainAlert, Severity
from core.application.services.planning.periode_conges_analyzer import (
    PeriodeCongesAnalyzer,
)


class CongesAnnuelRule(YearRule):
    """
    Règle annuelle RH sur les congés :

    - 28 jours de congés annuels (TypeJour.CONGE)
    - au moins une période de congés (congé + repos) de 15 jours consécutifs

    Comportement par année civile (via YearRule) :

    - Pour chaque année couverte par le contexte, YearRule appelle :
        check_year(context, year, year_start, year_end, is_full, work_days)

      où :
        - year_start = 01/01/year
        - year_end   = 31/12/year
        - work_days  = sous-ensemble des WorkDay de cette année dans l'intervalle
                       réellement couvert par le contexte
        - is_full    = True si le contexte couvre toute l'année civile
                       (du 1er janvier au 31 décembre)

    - Si is_full == True (année complète) :
        → erreurs bloquantes si quotas non respectés
    - Sinon :
        → uniquement des INFO de synthèse (aucune erreur bloquante)
    """

    name = "CongesAnnuelRule"
    description = "Contrôle annuel des congés (quotas et périodes longues)."

    MIN_CONGES_ANNUELS = 28
    MIN_CONGE_BLOCK = 15

    def __init__(self, analyzer: PeriodeCongesAnalyzer | None = None) -> None:
        self.analyzer = analyzer or PeriodeCongesAnalyzer()

    def check_year(
        self,
        context: PlanningContext,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        if not work_days:
            alerts.append(
                self.info(
                    f"[{year}] Aucun jour planifié sur cette année dans le contexte.",
                    code="CONGES_ANNUELS_EMPTY_YEAR",
                )
            )
            return True, alerts

        periodes = self.analyzer.detect_from_workdays(work_days)

        total_conges = sum(1 for wd in work_days if wd.type() == TypeJour.CONGE)

        longest_block = max((p.nb_jours for p in periodes), default=0)
        nb_blocks_15_plus = sum(
            1 for p in periodes if p.nb_jours >= self.MIN_CONGE_BLOCK
        )

        summary = (
            f"[{year}] Congés annuels : {total_conges} jour(s) pris. "
            f"Période de congés (congé+repos) la plus longue : {longest_block} jour(s). "
            f"Périodes de congés ≥ {self.MIN_CONGE_BLOCK} jours : {nb_blocks_15_plus}."
        )

        alerts.append(
            self.info(
                summary,
                code="CONGES_ANNUELS_SYNTHESIS",
            )
        )

        if is_full:
            if total_conges < self.MIN_CONGES_ANNUELS:
                alerts.append(
                    self.error(
                        msg=(
                            f"[{year}] Nombre de congés annuels insuffisant : "
                            f"{total_conges}/{self.MIN_CONGES_ANNUELS}."
                        ),
                        code="CONGES_ANNUELS_QUOTA_INSUFFISANT",
                    )
                )

            if nb_blocks_15_plus == 0:
                alerts.append(
                    self.error(
                        msg=(
                            f"[{year}] Aucune période de congés consécutifs "
                            f"(congé + repos) de {self.MIN_CONGE_BLOCK} jours ou plus détectée."
                        ),
                        code="CONGES_ANNUELS_BLOC_LONG_MANQUANT",
                    )
                )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
