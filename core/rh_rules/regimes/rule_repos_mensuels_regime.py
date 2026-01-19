from __future__ import annotations

from datetime import date
from typing import List, TYPE_CHECKING

from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.month_rule import MonthRule

if TYPE_CHECKING:
    from core.domain.entities import Regime

class RegimeReposMensuelsRule(MonthRule):
    """
    Monthly rest constraints driven by agent regime.

    For each FULL civil month:
      - At least N RPSD (Saturday->Sunday rest period)
      - At least M rest periods of >= 2 days total (including >=1 RPSD in practice)

    Partial month:
      - no blocking controls (silent)
    """

    name = "RegimeReposMensuelsRule"
    description = (
        "Contrôle mensuel des repos selon le régime : par mois complet, "
        "minimum RPSD et minimum périodes de repos de 2+ jours."
    )

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    def _get_regime(self, context: RhContext) -> Regime | None:
        return getattr(context.agent, "regime", None)

    def check(self, context: RhContext) -> RuleResult:
        # Not applicable if regime missing
        if self._get_regime(context) is None:
            return RuleResult.ok()
        return super().check(context)

    def check_month(
        self,
        context: RhContext,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        if not days:
            return RuleResult.ok()

        # Partial month -> silent (no enforcement)
        if not is_full:
            return RuleResult.ok()

        regime = self._get_regime(context)
        if regime is None:
            return RuleResult.ok()

        min_rpsd = int(regime.effective_min_rpsd)
        min_rp_2plus = int(regime.effective_min_rp_2plus)

        # Si un régime n’a pas de contrainte mensuelle configurée, on peut rendre la règle neutre.
        # (ex: min=0 ou None -> via effective_* tu peux choisir 0 si tu veux désactiver)
        if min_rpsd <= 0 and min_rp_2plus <= 0:
            return RuleResult.ok()

        summary = self.analyzer.summarize_rh_days(days)

        rpsd_count = 0
        rp_2plus_count = 0

        for p in summary.periods:
            if not (month_start <= p.start <= month_end):
                continue
            if p.nb_jours >= 2:
                rp_2plus_count += 1
            if p.is_rpsd():
                rpsd_count += 1

        if rpsd_count >= min_rpsd and rp_2plus_count >= min_rp_2plus:
            return RuleResult.ok()

        label = f"{year}-{month:02d}"
        regime_id = getattr(regime, "id", getattr(context.agent, "regime_id", None))
        regime_name = getattr(regime, "nom", "Inconnu")

        v = self.error_v(
            code="REGIME_MOIS_NON_CONFORME",
            msg=(
                f"[{label}] Régime {regime_name} - Repos mensuels insuffisants : "
                f"RPSD={rpsd_count} (min {min_rpsd}), "
                f"RP doubles/2+={rp_2plus_count} (min {min_rp_2plus})."
            ),
            start_date=month_start,
            end_date=month_end,
            meta={
                "year": year,
                "month": month,
                "label": label,
                "regime_id": regime_id,
                "regime_name": regime_name,
                "is_full": is_full,
                "rpsd": rpsd_count,
                "rp_2plus": rp_2plus_count,
                "min_rpsd": min_rpsd,
                "min_rp_2plus": min_rp_2plus,
                "total_rest_days": summary.total_rest_days,
                "total_rest_sundays": summary.total_rest_sundays,
            },
        )
        return RuleResult(violations=[v])
