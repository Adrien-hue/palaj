# core/application/services/agent_planning_validator_service.py
from __future__ import annotations

from core.domain.models.agent_planning import AgentPlanning
from core.rh_rules.adapters.planning_day_adapter import rh_context_from_planning_days
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.rh_rules_engine import RHRulesEngine
from core.utils.profiler import profiler


class AgentPlanningValidatorService:
    """
    RH-first validator: AgentPlanning -> RhContext -> EngineResult(RhViolation).
    """

    def __init__(self, rh_rules_engine: RHRulesEngine):
        self.rh_rules_engine = rh_rules_engine

    @profiler.profile_call()
    def validate(self, planning: AgentPlanning) -> RuleResult:
        ctx = rh_context_from_planning_days(
            agent=planning.agent,
            days=planning.days,
            window_start=planning.start_date,
            window_end=planning.end_date,
        )
        return self.rh_rules_engine.run(ctx)
