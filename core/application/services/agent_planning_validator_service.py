# core/application/services/agent_planning_validator_service.py
from typing import List

from core.utils.domain_alert import DomainAlert
from core.utils.profiler import profiler

from core.domain.contexts.planning_context import PlanningContext

from core.rh_rules.rh_rules_engine import RHRulesEngine

from core.domain.models.agent_planning import AgentPlanning

class AgentPlanningValidatorService:
    """
    Service de validation d'un planning d'agent :
    applique les règles RH via le moteur de règles.
    """

    def __init__(self, rh_rules_engine: RHRulesEngine):
        self.rh_rules_engine = rh_rules_engine

    @profiler.profile_call()
    def validate(self, planning: AgentPlanning) -> tuple[bool, List[DomainAlert]]:
        context = PlanningContext.from_planning(planning)

        ok, alerts = self.rh_rules_engine.run_for_context(context)
    
        return ok, alerts