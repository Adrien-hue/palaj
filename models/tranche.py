from datetime import time, datetime

class Tranche:
    def __init__(self, id: int, abbr: str, debut: time | str, fin: time | str, nb_agents_requis: int = 1):
        """
        Représente une tranche horaire de travail.

        :param id: Identifiant unique de la tranche
        :param abbr: Nom abrégé ou identifiant unique de la tranche (ex: 'MJ', 'RLIVM7P')
        :param debut: Heure de début (objet time ou chaîne 'HH:MM')
        :param fin: Heure de fin (objet time ou chaîne 'HH:MM')
        :param nb_agents_requis: Nombre d'agents nécessaires pour couvrir cette tranche
        """
        self.id = id
        self.abbr = abbr
        self.debut = self.__parse_heure(debut)
        self.fin = self.__parse_heure(fin)
        self.nb_agents_requis = nb_agents_requis

        self.validate()

    def __repr__(self):
        return f"Tranche({self.abbr}, {self.debut.strftime('%H:%M')} - {self.fin.strftime('%H:%M')}, durée={self.duree_formatee()})"
    
    def __str__(self):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        BLUE = "\033[94m"
        GRAY = "\033[90m"

        debut_str = self.debut.strftime("%H:%M") if self.debut else "Inconnue"
        fin_str = self.fin.strftime("%H:%M") if self.fin else "Inconnue"

        return (
            f"{BOLD}{BLUE}Tranche {self.abbr}{RESET}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Début:{RESET} {debut_str}\n"
            f"  {GRAY}Fin:{RESET} {fin_str}\n"
            f"  {GRAY}Durée:{RESET} {self.duree_formatee()}\n"
            f"  {GRAY}Nombre d'agents requis:{RESET} {self.nb_agents_requis}\n"
        )

    def __parse_heure(self, h):
        """
        Convertit une chaîne 'HH:MM' en objet datetime.time.
        """
        if isinstance(h, time) or h is None:
            return h
        try:
            return datetime.strptime(h, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Heure invalide pour la tranche {self.abbr}: {h}")

    def _calculer_duree_minutes(self) -> int:
        """
        Calcule la durée de la tranche en minutes.
        Gère les tranches passant minuit (ex: 22:00 → 06:20).
        """
        debut_minutes = self.debut.hour * 60 + self.debut.minute
        fin_minutes = self.fin.hour * 60 + self.fin.minute

        if fin_minutes < debut_minutes:  # Passage minuit
            fin_minutes += 24 * 60

        return fin_minutes - debut_minutes

    def duree(self) -> float:
        """
        Retourne la durée de la tranche en heures (arrondie à 2 décimales).
        """
        return round(self._calculer_duree_minutes() / 60, 2)

    def duree_formatee(self) -> str:
        """
        Retourne la durée au format 'XhYmin'.
        """
        total_min = self._calculer_duree_minutes()
        heures, minutes = divmod(total_min, 60)
        return f"{heures}h{minutes:02d}min"
    
    def validate(self):
        duree_heures = self.duree()
        if duree_heures > 11:
            raise ValueError(
                f"La tranche {self.abbr} a une durée de {duree_heures}h, "
                "ce qui dépasse la limite de 11h d'amplitude autorisée."
            )

    # --- JSON helpers ---
    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.abbr,
            "heure_debut": self.debut.strftime("%H:%M") if self.debut else None,
            "heure_fin": self.fin.strftime("%H:%M") if self.fin else None,
            "nb_agents_requis": self.nb_agents_requis,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            abbr=data["nom"],
            debut=data["heure_debut"],
            fin=data["heure_fin"],
            nb_agents_requis=data.get("nb_agents_requis", 1)
        )