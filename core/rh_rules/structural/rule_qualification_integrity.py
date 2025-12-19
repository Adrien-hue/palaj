# core/rh_rules/general/rule_qualification_integrity.py
from __future__ import annotations

from typing import List, Tuple, Set

from core.domain.contexts.planning_context import PlanningContext
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity


class QualificationIntegrityRule(BaseRule):
    name = "QualificationIntegrityRule"
    description = "Vérifie la cohérence tranches affectées ↔ qualifications (poste)."
    scope = RuleScope.PERIOD

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        if not context.work_days:
            return True, []

        # 1) Postes qualifiés (si vide => agent qualifié pour rien)
        qualified_postes: Set[int] = {q.poste_id for q in context.agent.qualifications}

        # 2) Postes rencontrés dans les tranches
        postes_travailles: Set[int] = set()
        for wd in context.work_days:
            if not wd.tranches:
                continue
            for t in wd.tranches:
                postes_travailles.add(t.poste_id)

        if not postes_travailles:
            return True, [
                self.info(
                    msg="Aucune tranche détectée : contrôle qualifications ignoré.",
                    code="QUALIF_NO_TRANCHES",
                )
            ]

        postes_non_qualifies = postes_travailles - qualified_postes

        # Si l'agent n'a aucune qualification, ici postes_non_qualifies == postes_travailles
        if not postes_non_qualifies:
            return True, [
                self.info(
                    msg="Toutes les affectations respectent les qualifications de l'agent.",
                    code="QUALIF_OK",
                )
            ]

        # Optionnel : message explicite quand aucune qualif
        if not qualified_postes:
            alerts.append(
                self.error(
                    msg=(
                        "Aucune qualification disponible pour l'agent : "
                        "toute affectation à un poste est considérée non qualifiée."
                    ),
                    code="QUALIF_EMPTY_SET",
                )
            )

        alerts.append(
            self.error(
                msg=(
                    f"Affectations non qualifiées détectées : "
                    f"{len(postes_non_qualifies)} poste(s) non couvert(s) par les qualifications."
                ),
                code="QUALIF_INVALID_POSTES",
            )
        )

        invalid_assignments = 0
        for wd in context.work_days:
            if not wd.tranches:
                continue
            for t in wd.tranches:
                if t.poste_id in postes_non_qualifies:
                    invalid_assignments += 1
                    alerts.append(
                        self.error(
                            msg=(
                                f"Affectation non qualifiée : poste_id={t.poste_id}, "
                                f"tranche={t.nom} (tranche_id={t.id})."
                            ),
                            jour=wd.jour,
                            code="QUALIF_ASSIGNMENT_INVALID",
                        )
                    )

        alerts.insert(
            0,
            self.error(
                msg=f"{invalid_assignments} affectation(s) non qualifiée(s) détectée(s).",
                code="QUALIF_INVALID_COUNT",
            )
        )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
