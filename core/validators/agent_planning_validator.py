from typing import List

from core.utils.domain_alert import DomainAlert, Severity

from core.domain.contexts.planning_context import PlanningContext

from core.rh_rules.rh_rules_engine import RHRulesEngine

from core.agent_planning import AgentPlanning



class AgentPlanningValidator:
    """
    Service de validation d'un planning complet d'agent sur une période.
    Travaille directement sur un objet AgentPlanning pour bénéficier
    des données déjà consolidées.
    """

    def __init__(
        self,
        rh_rules_engine: RHRulesEngine
    ):
        self.rh_rules_engine = rh_rules_engine

    def validate(self, planning: AgentPlanning) -> List[DomainAlert]:
        context = PlanningContext.from_planning(planning)

        _, alerts = self.rh_rules_engine.run_for_context(context)

        if all(a.severity in [Severity.SUCCESS, Severity.INFO] for a in alerts):
            alerts.append(
                DomainAlert(
                    f"Planning de {planning.agent.get_full_name()} cohérent ({planning.start_date} → {planning.end_date})",
                    Severity.SUCCESS,
                    source="AgentPlanningValidator",
                )
            )

        return alerts