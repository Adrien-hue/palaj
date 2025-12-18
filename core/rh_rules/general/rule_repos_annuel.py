from typing import List, Tuple
from datetime import date

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.year_rule import YearRule
from core.utils.domain_alert import DomainAlert, Severity

from core.application.services.planning.repos_stats_analyzer import ReposStatsAnalyzer


class ReposAnnuelRule(YearRule):
    """
    Règle annuelle RH :
    - Comptabilise RP simples, doubles, triples, 4+ jours
    - Compte RPSD (samedi→dimanche)
    - Compte WERP (samedi→dimanche ou dimanche→lundi)

    Comportement par année civile (via YearRule) :

    - Pour chaque année couverte par le contexte, YearRule appelle :
        check_year(context, year, year_start, year_end, is_full, work_days)

      où :
        - year_start = 01/01/year
        - year_end   = 31/12/year
        - work_days  = sous-ensemble des WorkDay de cette année dans l'intervalle
                       réellement couvert par le contexte
        - is_full    = True si le contexte couvre toute l'année civile

    - Si is_full == True (année complète) :
        → alerte ERROR si minima non atteints
    - Sinon :
        → alerte INFO de suivi uniquement
    """

    name = "ReposAnnuelRule"
    description = "Analyse annuelle des repos (RP, RP double, RPSD, WERP)."

    MIN_RP_DOUBLE = 52
    MIN_WERP = 14
    MIN_RPSD = 12

    def __init__(self, analyzer: ReposStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or ReposStatsAnalyzer()

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
                    code="REPOS_ANNUEL_EMPTY_YEAR",
                )
            )
            return True, alerts

        repos_summary = self.analyzer.summarize_workdays(work_days)

        if not repos_summary.periodes:
            alerts.append(
                self.info(
                    f"[{year}] Aucune période de repos détectée.",
                    code="REPOS_ANNUEL_AUCUN_REPOS",
                )
            )
            return True, alerts

        rp_simple = repos_summary.rp_simple
        rp_double = repos_summary.rp_double
        rp_triple = repos_summary.rp_triple
        rp_4plus = repos_summary.rp_4plus
        rpsd = repos_summary.rpsd
        werp = repos_summary.werp

        resume_info = (
            f"[{year}] Repos consécutifs détectés : "
            f"{rp_simple} simple(s), {rp_double} double(s), "
            f"{rp_triple} triple(s), {rp_4plus} de 4+ jours. "
            f"RPSD={rpsd}, WERP={werp}."
        )
        alerts.append(
            self.info(
                msg=resume_info,
                code="REPOS_ANNUEL_INFO",
            )
        )

        if not is_full:
            is_valid_partial = all(a.severity != Severity.ERROR for a in alerts)
            return is_valid_partial, alerts

        total_double_equiv = rp_double + rp_triple + rp_4plus

        if total_double_equiv < self.MIN_RP_DOUBLE:
            msg = (
                f"[{year}] Repos doubles insuffisants : "
                f"{total_double_equiv}/{self.MIN_RP_DOUBLE} "
                f"(dont {rp_triple} triples, {rp_4plus} de 4+ jours)."
            )
            alerts.append(
                self.error(
                    msg=msg,
                    code="REPOS_ANNUEL_RP_DOUBLE_INSUFFISANT",
                )
            )

        if werp < self.MIN_WERP:
            alerts.append(
                self.error(
                    msg=f"[{year}] WERP insuffisants : {werp}/{self.MIN_WERP}.",
                    code="REPOS_ANNUEL_WERP_INSUFFISANT",
                )
            )

        if rpsd < self.MIN_RPSD:
            alerts.append(
                self.error(
                    msg=f"[{year}] RPSD insuffisants : {rpsd}/{self.MIN_RPSD}.",
                    code="REPOS_ANNUEL_RPSD_INSUFFISANT",
                )
            )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
