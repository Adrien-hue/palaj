from dataclasses import dataclass
from datetime import date
from typing import List

@dataclass
class PeriodeRepos:
    start: date
    end: date
    jours: List[date]

    @property
    def nb_jours(self) -> int:
        return len(self.jours)

    @property
    def duree_minutes(self) -> int:
        """Durée totale de la période, incluant le repos quotidien de transition (12h20)."""
        return (self.nb_jours * 24 * 60) + (12 * 60 + 20)

    def label(self) -> str:
        """Retourne une étiquette lisible : RP simple, double, triple, etc."""
        if self.nb_jours == 1:
            return "RP simple"
        elif self.nb_jours == 2:
            return "RP double"
        elif self.nb_jours == 3:
            return "RP triple"
        else:
            return f"RP {self.nb_jours} jours"

    def __str__(self):
        return f"{self.label()} ({self.start} → {self.end}, {self.nb_jours}j)"