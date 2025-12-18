# core/rh_rules/rule_duree_moyenne_regime.py
from __future__ import annotations
from typing import List, Tuple
from datetime import date

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.domain.entities import TypeJour
from core.rh_rules.semester_rule import SemesterRule
from core.utils.domain_alert import DomainAlert, Severity

from core.rh_rules.constants.regime_rules import (
    REGIME_AVG_SERVICE_MINUTES,
    REGIME_AVG_TOLERANCE_MINUTES,
)


class DureeJourMoyenneSemestreRule(SemesterRule):
    """
    Vérifie la durée moyenne des journées de service en fonction du régime
    (B, B25, C...) sur chaque semestre civil.

    - Pour chaque semestre civil couvert par le PlanningContext :
      * si le semestre est **complet** dans le contexte :
          → ERROR si la moyenne nest pas dans la plage [objectif ± tolérance]
          → INFO sinon
      * si le semestre est **partiel** :
          → uniquement INFO récapitulatif (aucun blocage)
    """

    name = "DureeMoyenneJourneeRegimeRule"
    description = "Durée moyenne des journées de service par régime, calculée par semestre."

    # ---------- Garde globale avant de lancer l'analyse semestrielle ----------
    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        # 1) Pas de jours → rien à analyser
        if not context.work_days:
            return True, []

        agent = context.agent
        regime_id = getattr(agent, "regime_id", None)

        # 2) Règle non applicable si l'agent n'a pas de régime connu/configuré
        if regime_id is None or regime_id not in REGIME_AVG_SERVICE_MINUTES:
            return True, [
                self.info(
                    msg=(
                        "Règle de durée moyenne non applicable : "
                        "régime inconnu ou non configuré."
                    ),
                    code="SEM_DUREE_MOYENNE_REGIME_INCONNU",
                )
            ]

        # 3) Sinon on laisse SemesterRule découper par semestre
        return super().check(context)

    # ---------- Implémentation métier pour un semestre ----------
    def check_semester(
        self,
        context: PlanningContext,
        year: int,
        label: str,          # "S1" ou "S2"
        sem_start: date,
        sem_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        # Ici on sait déjà que le régime est valide (filtré dans check())
        agent = context.agent
        regime_id = getattr(agent, "regime_id", None)
        if regime_id is None or regime_id not in REGIME_AVG_SERVICE_MINUTES:
            # Sécurité : on considère que la règle est neutre pour ce semestre
            return True, []

        target = REGIME_AVG_SERVICE_MINUTES[regime_id]
        tol = REGIME_AVG_TOLERANCE_MINUTES

        # 1) Jours travaillés dans ce semestre (sur la portion couverte par le contexte)
        wd_semestre = [wd for wd in work_days if wd.is_working()]

        if not wd_semestre:
            alerts.append(
                self.info(
                    msg=f"{label} : aucun jour travaillé sur la période analysée.",
                    code="SEM_DUREE_MOYENNE_AUCUN_JOUR",
                    jour=sem_start,
                )
            )
            return True, alerts

        # 2) Calcul de la moyenne
        total_minutes = sum(wd.duree_minutes() for wd in wd_semestre)
        nb_jours_trav = len(wd_semestre)
        avg_minutes = total_minutes / nb_jours_trav

        h = int(avg_minutes // 60)
        m = int(avg_minutes % 60)
        h_target = target // 60
        m_target = target % 60

        base_msg = (
            f"{label} – durée moyenne de journée : "
            f"{h}h{m:02d} (objectif : {h_target}h{m_target:02d} ± {tol} min) "
            f"sur {nb_jours_trav} jour(s) travaillé(s)."
        )

        # 3) Semestre complet → contrôle strict
        if is_full:
            if abs(avg_minutes - target) > tol:
                alerts.append(
                    self.error(
                        msg=(
                            base_msg
                            + " Non conforme pour le semestre complet."
                        ),
                        code="SEM_DUREE_MOYENNE_NON_CONFORME",
                        jour=sem_end,
                    )
                )
            else:
                alerts.append(
                    self.info(
                        msg=(
                            base_msg
                            + " Conforme pour le semestre complet."
                        ),
                        code="SEM_DUREE_MOYENNE_CONFORME",
                        jour=sem_end,
                    )
                )
        else:
            # 4) Semestre partiel → info uniquement
            alerts.append(
                self.info(
                    msg=(
                        base_msg
                        + " Période incomplète : suivi indicatif uniquement."
                    ),
                    code="SEM_DUREE_MOYENNE_PARTIEL",
                    jour=sem_start,
                )
            )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
