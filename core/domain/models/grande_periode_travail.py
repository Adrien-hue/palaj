from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from core.domain.models.work_day import WorkDay

from core.utils.time_helpers import minutes_to_duree_str


@dataclass
class GrandePeriodeTravail:
    """
    Représente une Grande Période de Travail (GPT) :
    une suite de WorkDay consécutifs de type 'poste' ou 'zcot'.
    """

    workdays: List[WorkDay]
    is_left_truncated: bool = False
    is_right_truncated: bool = False

    # --- Propriétés dérivées ---
    @property
    def start(self) -> date:
        return min(wd.jour for wd in self.workdays)

    @property
    def end(self) -> date:
        return max(wd.jour for wd in self.workdays)

    @property
    def nb_jours(self) -> int:
        return len(self.workdays)

    @property
    def total_minutes(self) -> int:
        return sum(wd.duree_minutes() for wd in self.workdays)

    @property
    def has_zcot(self) -> bool:
        return any(wd.type() == "zcot" for wd in self.workdays)

    @property
    def has_poste(self) -> bool:
        return any(wd.type() == "poste" for wd in self.workdays)

    @property
    def has_absence(self) -> bool:
        return any(wd.type() == "absence" for wd in self.workdays)

    @property
    def has_conge(self) -> bool:
        return any(wd.type() == "conge" for wd in self.workdays)

    @property
    def has_nocturne(self) -> bool:
        return any(wd.is_nocturne() for wd in self.workdays)
    
    @property
    def is_truncated(self) -> bool:
        """Retourne True si la GPT touche une extrémité du contexte."""
        return self.is_left_truncated or self.is_right_truncated

    @property
    def is_complete(self) -> bool:
        """Retourne True si la GPT est totalement contenue dans le contexte."""
        return not self.is_truncated
    
    # --- Qualification de la GPT ---
    def is_absence_only(self) -> bool:
        """Retourne True si la GPT ne contient que des absences/congés."""
        return (self.has_absence or self.has_conge) and not (self.has_poste or self.has_zcot)

    def is_work_only(self) -> bool:
        """Retourne True si la GPT contient uniquement du travail (poste ou ZCOT)."""
        return (self.has_poste or self.has_zcot) and not (self.has_absence or self.has_conge)

    def is_mixed(self) -> bool:
        """Retourne True si la GPT mélange travail et absence/congé."""
        return (
            (self.has_poste or self.has_zcot)
            and (self.has_absence or self.has_conge)
        )

    def is_empty(self) -> bool:
        """GPT sans travail ni absence/congé (rare / anomalie)."""
        return not (self.has_poste or self.has_zcot or self.has_absence or self.has_conge)

    def category(self) -> str:
        """Retourne un label lisible selon le contenu."""
        if self.is_empty():
            return "Vide"
        if self.is_absence_only():
            return "Absence / Congé"
        if self.is_work_only():
            return "Travail"
        if self.is_mixed():
            return "Mixte"
        return "Inconnu"

    # --- Méthodes ---
    def contient(self, jour: date) -> bool:
        return self.start <= jour <= self.end

    def is_maximum(self) -> bool:
        """Retourne True si la GPT atteint la durée max réglementaire (6 jours)."""
        return self.nb_jours >= 6

    # --- Affichage enrichi ---
    def __str__(self) -> str:
        details = []
        if self.has_poste:
            details.append("Poste")
        if self.has_zcot:
            details.append("ZCOT")
        if self.has_absence:
            details.append("Absence")
        if self.has_conge:
            details.append("Congé")

        summary = ", ".join(details) if details else "—"
        return (
            f"GPT {self.start} → {self.end} "
            f"({self.nb_jours} jours, {minutes_to_duree_str(self.total_minutes)}) [{summary}]"
        )

    # --- Fabrique à partir de WorkDays ---
    @classmethod
    def from_workdays(cls, days: List[WorkDay], is_left_truncated: bool = False, is_right_truncated: bool = False) -> Optional["GrandePeriodeTravail"]:
        """
        Construit une GPT à partir d'une liste **consécutive** de WorkDays travaillés.
        Renvoie None si la liste est vide.
        """
        if not days:
            return None
        # Vérification de la continuité
        sorted_days = sorted(days, key=lambda wd: wd.jour)
        for i in range(1, len(sorted_days)):
            if (sorted_days[i].jour - sorted_days[i - 1].jour).days != 1:
                raise ValueError("Les WorkDays fournis ne sont pas consécutifs.")
        return cls(workdays=sorted_days, is_left_truncated=is_left_truncated, is_right_truncated=is_right_truncated)
