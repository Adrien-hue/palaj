from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

@dataclass
class PeriodeRepos:
    jours: List[date]

    @property
    def duree_minutes(self) -> int:
        """Durée totale de la période, incluant le repos quotidien de transition (12h20)."""
        return (self.nb_jours * 24 * 60) + (12 * 60 + 20)
    
    @property
    def end(self):
        return max(self.jours)

    @property
    def nb_jours(self) -> int:
        return len(self.jours)
    
    @property
    def start(self):
        return min(self.jours)
    
    def is_simple(self) -> bool:
        return self.nb_jours == 1

    def is_double(self) -> bool:
        return self.nb_jours == 2

    def is_triple(self) -> bool:
        return self.nb_jours == 3

    def is_4plus(self) -> bool:
        return self.nb_jours >= 4
    
    def is_rpsd(self) -> bool:
        """
        RPSD = au moins un couple consécutif samedi → dimanche
        dans la période de repos.
        """
        if self.nb_jours < 2:
            return False

        jours_sorted = sorted(self.jours)

        for d1, d2 in zip(jours_sorted, jours_sorted[1:]):
            # Vérifie qu'ils sont consécutifs (par sécurité)
            if (d2 - d1).days != 1:
                continue

            if d1.weekday() == 5 and d2.weekday() == 6:  # 5=sam, 6=dim
                return True

        return False

    def is_werp(self) -> bool:
        """
        WERP = au moins un couple consécutif :
        - samedi → dimanche, ou
        - dimanche → lundi
        """
        if self.nb_jours < 2:
            return False

        jours_sorted = sorted(self.jours)

        for d1, d2 in zip(jours_sorted, jours_sorted[1:]):
            if (d2 - d1).days != 1:
                continue

            # samedi → dimanche
            if d1.weekday() == 5 and d2.weekday() == 6:
                return True
            # dimanche → lundi
            if d1.weekday() == 6 and d2.weekday() == 0:
                return True

        return False


    def __str__(self):
        return f"Repos ({self.start} → {self.end}, {self.nb_jours}j)"
    
    @classmethod
    def from_days(cls, jours: List[date]) -> "PeriodeRepos":
        """
        Construit une PeriodeRepos à partir d'une liste de dates.
        Vérifie :
        - liste non vide
        - dates triées automatiquement
        - dates consécutives strictement (écart = 1 jour)
        """
        if not jours:
            raise ValueError("from_days() nécessite au moins une date.")

        days_sorted = sorted(jours)

        # Vérification de la consécutivité
        for d1, d2 in zip(days_sorted, days_sorted[1:]):
            if (d2 - d1).days != 1:
                raise ValueError(
                    f"Dates non consécutives détectées : {d1} → {d2}"
                )

        return cls(
            jours=days_sorted
        )