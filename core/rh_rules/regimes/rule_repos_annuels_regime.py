from __future__ import annotations

from datetime import date
from typing import List, TYPE_CHECKING

from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.year_rule import YearRule

if TYPE_CHECKING:
    from core.domain.entities import Regime

class RegimeReposAnnuelsRule(YearRule):
    """
    Annual periodic rest constraints driven by agent regime.

    Full civil year requirements (depending on regime):
    - At least N periodic rest days (RP)
    - Including at least M Sundays of rest

    Partial year:
    - no blocking controls (errors-only engine)
    """

    name = "RegimeReposAnnuelsRule"
    description = "Repos annuels (RP + dimanches) selon le régime de l'agent."

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    def _get_regime(self, context: RhContext) -> Regime | None:
        return getattr(context.agent, "regime", None)

    def check(self, context: RhContext) -> RuleResult:
        # Not applicable if regime missing
        if self._get_regime(context) is None:
            return RuleResult.ok()
        return super().check(context)

    def check_year(
        self,
        context: RhContext,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        if not days:
            return RuleResult.ok()

        # Partial year => silent OK
        if not is_full:
            return RuleResult.ok()

        regime = self._get_regime(context)
        if regime is None:
            return RuleResult.ok()

        repos_summary = self.analyzer.summarize_rh_days(days)
        total_rest_days = repos_summary.total_rest_days
        total_rest_sundays = repos_summary.total_rest_sundays

        min_rp_annuels = int(regime.effective_min_rp_annuels)
        min_rp_dimanches = int(regime.effective_min_rp_dimanches)

        regime_id = getattr(regime, "id", getattr(context.agent, "regime_id", None))
        regime_name = getattr(regime, "nom", "Inconnu")

        violations: List[RhViolation] = []

        if total_rest_days < min_rp_annuels:
            violations.append(
                self.error_v(
                    code="REGIME_REPOS_RP_INSUFFISANTS",
                    msg=(
                        f"[{year}] Repos périodiques insuffisants pour le régime {regime_name} : "
                        f"{total_rest_days}/{min_rp_annuels} jours sur l'année."
                    ),
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "regime_id": regime_id,
                        "regime_name": regime_name,
                        "total_rest_days": total_rest_days,
                        "min_required": min_rp_annuels,
                    },
                )
            )

        if total_rest_sundays < min_rp_dimanches:
            violations.append(
                self.error_v(
                    code="REGIME_REPOS_DIMANCHES_INSUFFISANTS",
                    msg=(
                        f"[{year}] Dimanches de repos insuffisants pour le régime {regime_name} : "
                        f"{total_rest_sundays}/{min_rp_dimanches} dimanches sur l'année."
                    ),
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "regime_id": regime_id,
                        "regime_name": regime_name,
                        "total_rest_sundays": total_rest_sundays,
                        "min_required": min_rp_dimanches,
                    },
                )
            )

        return RuleResult(violations=violations)
