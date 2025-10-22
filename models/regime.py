from __future__ import annotations

class Regime:
    def __init__(self, id: int, nom: str, desc: str = "", duree_moyenne_journee_service_min: int = 0, repos_periodiques_annuels: int = 0):
        """
        Initialise un régime avec un nom et une description.

        :param nom: Le nom du régime
        :param desc: La description du régime
        """
        self.id = id
        self.nom = nom
        self.desc = desc
        self.duree_moyenne_journee_service_min = duree_moyenne_journee_service_min
        self.repos_periodiques_annuels = repos_periodiques_annuels

    def __repr__(self):
        heures = self.duree_moyenne_journee_service_min // 60
        minutes = self.duree_moyenne_journee_service_min % 60
        return (
            f"<Regime id={self.id}, nom='{self.nom}', "
            f"duree_moy={heures}h{minutes:02d}min, repos_annuels={self.repos_periodiques_annuels}>"
        )
    
    def __str__(self):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        BLUE = "\033[94m"
        GRAY = "\033[90m"
        YELLOW = "\033[93m"

        heures = self.duree_moyenne_journee_service_min // 60
        minutes = self.duree_moyenne_journee_service_min % 60
        duree_str = f"{heures}h{minutes:02d}min" if self.duree_moyenne_journee_service_min else "Inconnue"

        return (
            f"{BOLD}{BLUE}Régime {self.nom}{RESET}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Description:{RESET} {self.desc or 'Aucune'}\n"
            f"  {GRAY}Durée moyenne journée:{RESET} {YELLOW}{duree_str}{RESET}\n"
            f"  {GRAY}Repos périodiques annuels:{RESET} {self.repos_periodiques_annuels}\n"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "desc": self.desc,
            "duree_moyenne_journee_service_min": self.duree_moyenne_journee_service_min,
            "repos_periodiques_annuels": self.repos_periodiques_annuels,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Regime:
        return cls(
            id=data["id"],
            nom=data["nom"],
            desc=data.get("desc") or "",
            duree_moyenne_journee_service_min=data.get("duree_moyenne_journee_service_min") or 0,
            repos_periodiques_annuels=data.get("repos_periodiques_annuels") or 0,
        )