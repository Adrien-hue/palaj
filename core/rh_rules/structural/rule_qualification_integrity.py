# core/rh_rules/structural/rule_qualification_integrity.py
from __future__ import annotations

from typing import List, Tuple, Set

from core.application.services.container import qualification_service
from core.domain.contexts.planning_context import PlanningContext
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity


class QualificationIntegrityRule(BaseRule):
    """
    Contrôle d'intégrité : chaque tranche travaillée doit correspondre
    à un poste pour lequel l'agent est qualifié.

    - Pré-check global via set(poste_id) pour limiter le coût.
    - Si problème détecté, on émet des erreurs datées (jour + tranche).
    """

    name = "QualificationIntegrityRule"
    description = "Vérifie la cohérence tranches affectées ↔ qualifications (poste)."
    scope = RuleScope.PERIOD

    def __init__(self):
        self.qualification_service = qualification_service

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        if not context.work_days:
            return True, []

        agent_id = context.agent.id
        if agent_id is None:
            return False, [
                self.error(
                    msg="Impossible de vérifier les qualifications : agent.id manquant.",
                    code="QUALIF_AGENT_ID_MISSING",
                )
            ]

        # -----------------------------------------
        # 1) Pré-check global : postes réellement vus
        # -----------------------------------------
        postes_travailles: Set[int] = set()

        for wd in context.work_days:
            # Si ton modèle garantit que POSTE => tranches non vides,
            # pas besoin de wd.is_working(). On peut juste regarder tranches.
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

        postes_non_qualifies = {
            poste_id
            for poste_id in postes_travailles
            if not self.qualification_service.is_qualified(agent_id, poste_id)
        }

        if not postes_non_qualifies:
            return True, [
                self.info(
                    msg="Toutes les affectations respectent les qualifications de l'agent.",
                    code="QUALIF_OK",
                )
            ]

        # ------------------------------------------------------
        # 2) Détails : on liste quand et sur quelles tranches
        # ------------------------------------------------------
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
            1,
            self.error(
                msg=f"{invalid_assignments} affectation(s) non qualifiée(s) détectée(s).",
                code="QUALIF_INVALID_COUNT",
            )
        )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
