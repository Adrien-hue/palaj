from datetime import date, time, timedelta
from typing import List, Optional

from core.utils.time_helpers import minutes_to_duree_str

from core.domain.entities import EtatJourAgent, Tranche, TypeJour

class WorkDay:
    """
    Représente une journée planifiée (poste, zcot, repos, congé, absence).
    Elle encapsule la logique de durée et de classification RH.
    """
    HEURE_NUIT_DEBUT = time(21, 30)
    HEURE_NUIT_FIN = time(6, 30)

    COLOR_RESET = "\033[0m"
    COLOR_GREEN = "\033[92m"
    COLOR_BLUE = "\033[94m"
    COLOR_YELLOW = "\033[93m"
    COLOR_RED = "\033[91m"

    def __init__(
        self,
        jour: date,
        etat: Optional[EtatJourAgent] = None,
        tranches: Optional[List[Tranche]] = None,
    ):
        self.jour = jour
        self.etat = etat
        self.tranches = tranches or []

    # --- Typage RH -------------------------------------------------
    def type(self) -> TypeJour:
        if self.etat:
            return self.etat.type_jour
        return TypeJour.POSTE if self.tranches else TypeJour.INCONNU

    def is_working(self) -> bool:
        return self.type() in (TypeJour.POSTE, TypeJour.ZCOT)

    def is_rest(self) -> bool:
        return self.type() in (TypeJour.REPOS, TypeJour.CONGE)

    def is_absence(self) -> bool:
        return self.type() == TypeJour.ABSENCE
    
    def is_nocturne(self) -> bool:
        """Retourne True si la journée comporte au moins une tranche de nuit."""
        if not self.tranches:
            return False

        for t in self.tranches:
            if self._tranche_is_nocturne(t):
                return True
        return False
    
    def _tranche_is_nocturne(self, tranche: Tranche) -> bool:
        """Détermine si une tranche intersecte la période nocturne."""
        debut, fin = tranche.heure_debut, tranche.heure_fin
        return (debut >= self.HEURE_NUIT_DEBUT) or (fin <= self.HEURE_NUIT_FIN)

    # --- Durées -----------------------------------------------------
    def amplitude_minutes(self) -> int:
        """Amplitude totale de la journée (en minutes)."""
        if not self.tranches:
            return 0
        
        start = self.start_time()
        end = self.end_time()

        if not start or not end:
            return 0

        delta = timedelta(hours=end.hour, minutes=end.minute) - timedelta(hours=start.hour, minutes=start.minute)
        minutes = int(delta.total_seconds() / 60)
        if minutes < 0:
            minutes += 24 * 60  # passage minuit
        return minutes

    def amplitude_hours(self) -> float:
        """Conversion utilitaire pour compatibilité (en heures)."""
        return self.amplitude_minutes() / 60.0
    
    def duree_minutes(self) -> int:
        """
        Retourne la durée totale travaillée de la journée en minutes.
        - Si journée POSTE → somme des durées de chaque tranche.
        - Si journée ZCOT → 7h fixes (420 minutes).
        - Sinon → 0 minute.
        """
        if self.is_rest():
            return 0

        # Cas ZCOT : journée "bureau" à durée fixe
        if self.type() == TypeJour.ZCOT:
            return 7 * 60  # 7h00 = 420 minutes

        # Cas POSTE : somme réelle des durées de tranches
        if self.tranches:
            total = 0
            for t in self.tranches:
                total += int(t.duree_minutes())
            return total

        return 0
    
    def duree_hours(self) -> float:
        """Durée totale travaillée (en heures)."""
        if self.type() == TypeJour.ZCOT:
            return 12.0
        if self.type() == TypeJour.POSTE:
            return sum(t.duree() for t in self.tranches)
        return 0.0
    
    def start_time(self) -> Optional[time]:
        """Heure de début de la première tranche."""
        if not self.tranches:
            return None
        return min(t.heure_debut for t in self.tranches)

    def end_time(self) -> Optional[time]:
        """Heure de fin de la dernière tranche."""
        if not self.tranches:
            return None
        return max(t.heure_fin for t in self.tranches)

    # --- Représentation ---------------------------------------------
    def __repr__(self):
        return f"WorkDay({self.jour}, {self.type().value}, {minutes_to_duree_str(self.duree_minutes())})"

    def __str__(self) -> str:
        """Retourne une représentation colorée lisible."""
        type_str = self.type().value.upper()
        duree_str = minutes_to_duree_str(self.duree_minutes())

        if self.is_working():
            color = self.COLOR_GREEN
        elif self.is_rest():
            color = self.COLOR_BLUE
        elif self.is_absence():
            color = self.COLOR_RED
        else:
            color = self.COLOR_YELLOW

        tranches_str = (
            ", ".join(f"{t.nom}({t.heure_debut.strftime('%H:%M')}-{t.heure_fin.strftime('%H:%M')})"
                      for t in self.tranches)
            if self.tranches else "-"
        )

        return (
            f"{color}{self.jour.strftime('%Y-%m-%d')} | "
            f"{type_str:<7} | {duree_str:<5} | Tranches: {tranches_str}{self.COLOR_RESET}"
        )