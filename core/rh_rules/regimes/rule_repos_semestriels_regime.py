from __future__ import annotations

from datetime import date
from typing import List, TYPE_CHECKING

from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.semester_rule import SemesterRule

if TYPE_CHECKING:
    from core.domain.entities import Regime

class RegimeReposSemestrielsRule(SemesterRule):
    """
    Semester periodic rest constraints driven by agent regime.

    For each FULL civil semester:
      - At least N periodic rest days (RP) per semester:
        - S1: 01/01 -> 30/06
        - S2: 01/07 -> 31/12

    Partial semester:
      - no blocking controls (silent)
    """

    name = "RegimeReposSemestrielsRule"
    description = "Repos semestriels (RP) selon le régime de l'agent."

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    def _get_regime(self, context: RhContext) -> Regime | None:
        return getattr(context.agent, "regime", None)

    def check(self, context: RhContext) -> RuleResult:
        if self._get_regime(context) is None:
            return RuleResult.ok()
        return super().check(context)

    def check_semester(
        self,
        context: RhContext,
        year: int,
        label: str,  # "S1" or "S2"
        sem_start: date,
        sem_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        if not days:
            return RuleResult.ok()

        # Partial semester -> silent
        if not is_full:
            return RuleResult.ok()

        regime = self._get_regime(context)
        if regime is None:
            return RuleResult.ok()

        min_rp_semestre = int(regime.effective_min_rp_semestre)

        # Si un régime n’a pas de contrainte semestrielle configurée,
        # on peut rendre la règle neutre.
        if min_rp_semestre <= 0:
            return RuleResult.ok()

        summary = self.analyzer.summarize_rh_days(days)
        nb_rp_sem = summary.total_rest_days

        if nb_rp_sem >= min_rp_semestre:
            return RuleResult.ok()

        regime_id = getattr(regime, "id", getattr(context.agent, "regime_id", None))
        regime_name = getattr(regime, "nom", "Inconnu")

        v: RhViolation = self.error_v(
            code="REGIME_SEMESTRE_RP_INSUFFISANTS",
            msg=(
                f"[{year} {label}] Repos périodiques insuffisants pour le régime {regime_name} "
                f"sur le semestre {sem_start} → {sem_end} : "
                f"{nb_rp_sem}/{min_rp_semestre} jours."
            ),
            start_date=sem_start,
            end_date=sem_end,
            meta={
                "year": year,
                "label": label,
                "regime_id": regime_id,
                "regime_name": regime_name,
                "is_full": is_full,
                "total_rest_days": nb_rp_sem,
                "min_required": min_rp_semestre,
                "total_rest_sundays": summary.total_rest_sundays,
            },
        )
        return RuleResult(violations=[v])
