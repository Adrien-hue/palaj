from abc import ABC, abstractmethod
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert


class DayRule(BaseRule, ABC):
    """
    Règle appliquée à un seul WorkDay à la fois.

    Le moteur RH :
      - boucle sur les WorkDay triés
      - pour chaque WorkDay :
          * context.date_reference = wd.jour
          * context.current_work_day = wd
      - appelle rule.check(context)

    Ici, on factorise :
      - check() récupère le WorkDay de référence
      - délègue à check_day(context, work_day)
    """

    scope = RuleScope.DAY

    @abstractmethod
    def check_day(
        self,
        context: PlanningContext,
        work_day: WorkDay,
    ) -> Tuple[bool, List[DomainAlert]]:
        """Implémentation métier sur UNE journée (un WorkDay)."""
        raise NotImplementedError

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        work_day = context.current_work_day

        if work_day is None:
            return False, [
                self.error(
                    "Impossible de déterminer le WorkDay de référence pour une règle journalière.",
                    code="DAY_NO_WORKDAY_REFERENCE",
                )
            ]

        return self.check_day(context, work_day)
