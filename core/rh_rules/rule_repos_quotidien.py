from datetime import datetime, timedelta

from core.domain.contexts.planning_context import PlanningContext
from .base_rule import BaseRule

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.tranche_repo import TrancheRepository

class ReposQuotidienRule(BaseRule):
    """
    Règle RH : Durée de repos quotidien.
        - 12h20 minimum entre deux journées de travail.
        - 14h si la journée précédente contient plus de 2h30 de travail entre 21:30 et 6:30.
    """

    REPOS_MIN = timedelta(hours=12, minutes=20)
    REPOS_MIN_APRES_NUIT = timedelta(hours=14)
    NUIT_START = 21.5  # 21h30
    NUIT_END = 6.5     # 06h30
    NUIT_SEUIL = 2.5   # heures

    def __init__(self, tranche_repo: TrancheRepository, affectation_repo: AffectationRepository):
        self.tranche_repo = tranche_repo
        self.affectation_repo = affectation_repo

    # ------------------------------------------------------------
    def check(self, context: PlanningContext) -> list[str]:
        alerts = []
        all_affectations = sorted(context.get_all_affectations(), key=lambda a: a.jour)

        # On compare chaque jour travaillé au suivant
        for i in range(1, len(all_affectations)):
            prev = all_affectations[i - 1]
            curr = all_affectations[i]

            if context.date_reference and curr.jour != context.date_reference:
                continue

            # Si plus d'un jour d'écart, le repos est forcément respecté
            if (curr.jour - prev.jour).days > 1:
                continue

            prev_tranche = self.tranche_repo.get(prev.tranche_id)
            curr_tranche = self.tranche_repo.get(curr.tranche_id)

            if not prev_tranche or not curr_tranche:
                alerts.append(f"{context.agent.get_full_name()} : tranche manquante pour l'affectation {prev.id} ou {curr.id}")
                continue

            # Calcul du repos effectif entre les deux journées
            prev_end = datetime.combine(prev.jour, prev_tranche.fin)
            curr_start = datetime.combine(curr.jour, curr_tranche.debut)

            # Gestion du passage de minuit
            if curr_start < prev_end:
                curr_start += timedelta(days=1)

            repos_effectif = curr_start - prev_end

            # Seuil adapté selon la présence de travail de nuit
            seuil = self.REPOS_MIN_APRES_NUIT if self._contains_night_work(prev_tranche) else self.REPOS_MIN

            if repos_effectif < seuil:
                alerts.append(
                    f"⚠️ {context.agent.get_full_name()} : repos insuffisant entre "
                    f"{prev.jour} ({prev_tranche.abbr}) et {curr.jour} ({curr_tranche.abbr}) "
                    f"→ {repos_effectif.total_seconds()/3600:.2f}h < {seuil.total_seconds()/3600:.2f}h"
                )

        return alerts

    # ------------------------------------------------------------
    def _contains_night_work(self, tranche) -> bool:
        """Vérifie si une tranche contient plus de 2h30 de travail de nuit (entre 21h30 et 6h30)."""
        start_h = tranche.debut.hour + tranche.debut.minute / 60
        end_h = tranche.fin.hour + tranche.fin.minute / 60

        # Cas classique (pas de passage minuit)
        if start_h < end_h:
            duree_nuit = self._overlap_hours(start_h, end_h, self.NUIT_START, 24) + \
                         self._overlap_hours(start_h, end_h, 0, self.NUIT_END)
        else:
            # Passage minuit : deux parties à traiter
            duree_nuit = self._overlap_hours(start_h, 24, self.NUIT_START, 24) + \
                         self._overlap_hours(0, end_h, 0, self.NUIT_END)

        return duree_nuit >= self.NUIT_SEUIL

    # ------------------------------------------------------------
    def _overlap_hours(self, start1, end1, start2, end2) -> float:
        """Calcule le chevauchement entre deux intervalles horaires."""
        start = max(start1, start2)
        end = min(end1, end2)
        return max(0, end - start)
