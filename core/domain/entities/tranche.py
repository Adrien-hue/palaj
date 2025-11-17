from datetime import time, datetime
from typing import Optional

from core.domain.entities import Poste

class Tranche:
    def __init__(self, id: int, nom: str, heure_debut: time | str, heure_fin: time | str, poste_id: int):
        """
        Représente une tranche horaire de travail.

        :param id: Identifiant unique de la tranche
        :param nom: Nom abrégé ou identifiant unique de la tranche (ex: 'MJ', 'RLIVM7P')
        :param heure_debut: Heure de début (objet time ou chaîne 'HH:MM')
        :param heure_fin: Heure de fin (objet time ou chaîne 'HH:MM')
        :param poste_id: Identifiant du poste associé à cette tranche
        """
        self.id = id
        self.nom = nom
        self.heure_debut = self.__parse_heure(heure_debut)
        self.heure_fin = self.__parse_heure(heure_fin)
        self.poste_id = poste_id

        self._poste: Poste | None = None

    def __repr__(self):
        return f"Tranche({self.nom}, {self.heure_debut.strftime('%H:%M')} - {self.heure_fin.strftime('%H:%M')}, durée={self.duree_formatee()}, poste_id={self.poste_id})"
    
    def __str__(self):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        BLUE = "\033[94m"
        GRAY = "\033[90m"

        debut_str = self.heure_debut.strftime("%H:%M") if self.heure_debut else "Inconnue"
        fin_str = self.heure_fin.strftime("%H:%M") if self.heure_fin else "Inconnue"

        return (
            f"{BOLD}{BLUE}Tranche {self.nom}{RESET}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Début:{RESET} {debut_str}\n"
            f"  {GRAY}Fin:{RESET} {fin_str}\n"
            f"  {GRAY}Durée:{RESET} {self.duree_formatee()}\n"
            f"  {GRAY}poste_id:{RESET} {self.poste_id}\n"
        )
    
    # Getters / Setters
    @property
    def poste(self) -> Poste | None:
        return self._poste
    
    def set_poste(self, poste: Optional[Poste]) -> None:
        self._poste = poste

    # Méthodes privées
    def __parse_heure(self, h):
        """
        Convertit une chaîne 'HH:MM' en objet datetime.time.
        """
        if isinstance(h, time) or h is None:
            return h
        try:
            return datetime.strptime(h, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Heure invalide pour la tranche {self.nom}: {h}")

    # Méthodes publiques
    def duree_minutes(self) -> int:
        """
        Calcule la durée de la tranche en minutes.
        Gère les tranches passant minuit (ex: 22:00 → 06:20).
        """
        debut_minutes = self.heure_debut.hour * 60 + self.heure_debut.minute
        fin_minutes = self.heure_fin.hour * 60 + self.heure_fin.minute

        if fin_minutes < debut_minutes:  # Passage minuit
            fin_minutes += 24 * 60

        return fin_minutes - debut_minutes

    def duree(self) -> float:
        """
        Retourne la durée de la tranche en heures (arrondie à 2 décimales).
        """
        return round(self.duree_minutes() / 60, 2)

    def duree_formatee(self) -> str:
        """
        Retourne la durée au format 'XhYmin'.
        """
        total_min = self.duree_minutes()
        heures, minutes = divmod(total_min, 60)
        return f"{heures}h{minutes:02d}min"

    # --- JSON helpers ---
    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "heure_debut": self.heure_debut.strftime("%H:%M") if self.heure_debut else None,
            "heure_fin": self.heure_fin.strftime("%H:%M") if self.heure_fin else None,
            "poste_id": self.poste_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            nom=data["nom"],
            heure_debut=data["heure_debut"],
            heure_fin=data["heure_fin"],
            poste_id=data["poste_id"],
        )