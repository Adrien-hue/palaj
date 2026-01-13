# core/rh_rules/structural/rule_qualification_integrity.py
from __future__ import annotations

from typing import List, Set

from core.rh_rules.base_rule import BaseRule
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.models.rule_scope import RuleScope


class QualificationIntegrityRule(BaseRule):
    """
    Integrity rule:
    - Collect poste_id encountered in working intervals
    - Compare to agent qualifications (poste_id)
    - Report:
        * QUALIF_EMPTY_SET if agent has no qualifications but works on poste_id
        * QUALIF_INVALID_POSTES + per-assignment details if unqualified poste(s) found
    """

    name = "QualificationIntegrityRule"
    description = "Vérifie la cohérence tranches affectées ↔ qualifications (poste)."
    scope = RuleScope.PERIOD

    def check(self, context: RhContext) -> RuleResult:
        if not context.days:
            return RuleResult.ok()

        # 1) Qualified postes (agent)
        qualifications = getattr(context.agent, "qualifications", None) or []
        qualified_postes: Set[int] = {q.poste_id for q in qualifications if getattr(q, "poste_id", None) is not None}

        # 2) Postes encountered in worked intervals (only if poste_id is set)
        postes_travailles: Set[int] = set()
        for day in context.days:
            if not day.intervals:
                continue
            for itv in day.intervals:
                if itv.poste_id is not None:
                    postes_travailles.add(itv.poste_id)

        # If agent never worked on a poste_id (no postes to validate) -> OK
        if not postes_travailles:
            return RuleResult.ok()

        postes_non_qualifies = postes_travailles - qualified_postes

        # If everything is qualified -> OK
        if not postes_non_qualifies:
            return RuleResult.ok()

        violations: List[RhViolation] = []

        # If agent has no qualifications but has postes worked -> explicit error
        if not qualified_postes:
            violations.append(
                self.error_v(
                    code="QUALIF_EMPTY_SET",
                    msg=(
                        "Aucune qualification disponible pour l'agent : "
                        "toute affectation à un poste est considérée non qualifiée."
                    ),
                    start_date=context.effective_start,
                    end_date=context.effective_end,
                    meta={
                        "worked_postes": sorted(postes_travailles),
                    },
                )
            )

        # Global invalid postes summary
        violations.append(
            self.error_v(
                code="QUALIF_INVALID_POSTES",
                msg=(
                    "Affectations non qualifiées détectées : "
                    f"{len(postes_non_qualifies)} poste(s) non couvert(s) par les qualifications."
                ),
                start_date=context.effective_start,
                end_date=context.effective_end,
                meta={
                    "qualified_postes": sorted(qualified_postes),
                    "worked_postes": sorted(postes_travailles),
                    "unqualified_postes": sorted(postes_non_qualifies),
                },
            )
        )

        # Per-assignment details
        invalid_assignments = 0
        for day in context.days:
            if not day.intervals:
                continue
            for itv in day.intervals:
                if itv.poste_id is None:
                    continue
                if itv.poste_id in postes_non_qualifies:
                    invalid_assignments += 1
                    violations.append(
                        self.error_v(
                            code="QUALIF_ASSIGNMENT_INVALID",
                            msg=(
                                "Affectation non qualifiée : "
                                f"poste_id={itv.poste_id}, "
                                f"interval={getattr(itv, 'nom', None) or 'N/A'} "
                                f"(interval_id={getattr(itv, 'id', None)})"
                            ),
                            start_date=day.day_date,
                            end_date=day.day_date,
                            meta={
                                "poste_id": itv.poste_id,
                                "interval_id": getattr(itv, "id", None),
                                "interval_name": getattr(itv, "nom", None),
                                "day": day.day_date.isoformat(),
                            },
                        )
                    )

        # Count header (inserted first)
        violations.insert(
            0,
            self.error_v(
                code="QUALIF_INVALID_COUNT",
                msg=f"{invalid_assignments} affectation(s) non qualifiée(s) détectée(s).",
                start_date=context.effective_start,
                end_date=context.effective_end,
                meta={
                    "invalid_assignments": invalid_assignments,
                    "unqualified_postes": sorted(postes_non_qualifies),
                },
            )
        )

        return RuleResult(violations=violations)
