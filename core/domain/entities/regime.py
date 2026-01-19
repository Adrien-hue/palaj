from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from core.domain.entities import Agent


class Regime:
    DEFAULT_MIN_RP_ANNUELS = 114
    DEFAULT_MIN_RP_DIMANCHES = 52

    DEFAULT_MIN_RPSD = 0
    DEFAULT_MIN_RP_2PLUS = 0

    DEFAULT_MIN_RP_SEMESTRE = 56

    DEFAULT_AVG_SERVICE_MINUTES = 465
    DEFAULT_AVG_TOLERANCE_MINUTES = 5

    def __init__(
        self,
        id: int,
        nom: str,
        desc: str = "",

        min_rp_annuels: Optional[int] = None,
        min_rp_dimanches: Optional[int] = None,

        min_rpsd: Optional[int] = None,
        min_rp_2plus: Optional[int] = None,

        min_rp_semestre: Optional[int] = None,

        avg_service_minutes: Optional[int] = None,
        avg_tolerance_minutes: Optional[int] = None,
    ):
        self.id = id
        self.nom = nom
        self.desc = desc

        self.min_rp_annuels = min_rp_annuels
        self.min_rp_dimanches = min_rp_dimanches

        self.min_rpsd = min_rpsd
        self.min_rp_2plus = min_rp_2plus

        self.min_rp_semestre = min_rp_semestre

        self.avg_service_minutes = avg_service_minutes
        self.avg_tolerance_minutes = avg_tolerance_minutes

        self._agents: Optional[List[Agent]] = None

    # -------------------------
    # Valeurs effectives (fallback)
    # -------------------------
    @property
    def effective_min_rp_annuels(self) -> int:
        return self.min_rp_annuels if self.min_rp_annuels is not None else self.DEFAULT_MIN_RP_ANNUELS

    @property
    def effective_min_rp_dimanches(self) -> int:
        return self.min_rp_dimanches if self.min_rp_dimanches is not None else self.DEFAULT_MIN_RP_DIMANCHES

    @property
    def effective_min_rpsd(self) -> int:
        return self.min_rpsd if self.min_rpsd is not None else self.DEFAULT_MIN_RPSD

    @property
    def effective_min_rp_2plus(self) -> int:
        return self.min_rp_2plus if self.min_rp_2plus is not None else self.DEFAULT_MIN_RP_2PLUS

    @property
    def effective_min_rp_semestre(self) -> int:
        return self.min_rp_semestre if self.min_rp_semestre is not None else self.DEFAULT_MIN_RP_SEMESTRE

    @property
    def effective_avg_tolerance_minutes(self) -> int:
        return (
            self.avg_tolerance_minutes
            if self.avg_tolerance_minutes is not None
            else self.DEFAULT_AVG_TOLERANCE_MINUTES
        )
    
    @property
    def effective_avg_service_minutes(self) -> int:
        return self.avg_service_minutes if self.avg_service_minutes is not None else self.DEFAULT_AVG_SERVICE_MINUTES

    # -------------------------
    # Relations (cache privé)
    # -------------------------
    @property
    def agents(self) -> Optional[List[Agent]]:
        return self._agents

    def set_agents(self, agents: Optional[List[Agent]]):
        self._agents = agents

    # -------------------------
    # Représentation
    # -------------------------
    def __repr__(self) -> str:
        return (
            f"<Regime id={self.id}, nom='{self.nom}', "
            f"avg_service_minutes={self.avg_service_minutes}, "
            f"min_rp_annuels={self.min_rp_annuels}>"
        )

    def __str__(self) -> str:
        RESET = "\033[0m"
        BOLD = "\033[1m"
        BLUE = "\033[94m"
        GRAY = "\033[90m"
        YELLOW = "\033[93m"

        avg_str = (
            f"{self.avg_service_minutes} min"
            if self.avg_service_minutes is not None
            else "Inconnue"
        )

        tol_str = f"{self.effective_avg_tolerance_minutes} min"

        return (
            f"{BOLD}{BLUE}Régime {self.nom}{RESET}\n"
            f"  {GRAY}ID:{RESET} {self.id}\n"
            f"  {GRAY}Description:{RESET} {self.desc or 'Aucune'}\n"
            f"  {GRAY}Moyenne service:{RESET} {YELLOW}{avg_str}{RESET}\n"
            f"  {GRAY}Tolérance moyenne:{RESET} {YELLOW}{tol_str}{RESET}\n"
            f"  {GRAY}RP annuels min:{RESET} {self.effective_min_rp_annuels}\n"
            f"  {GRAY}RP dimanches min:{RESET} {self.effective_min_rp_dimanches}\n"
            f"  {GRAY}RP SD min:{RESET} {self.effective_min_rpsd}\n"
            f"  {GRAY}RP 2+ min:{RESET} {self.effective_min_rp_2plus}\n"
            f"  {GRAY}RP semestre min:{RESET} {self.effective_min_rp_semestre}\n"
        )

    # -------------------------
    # Serialization
    # -------------------------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nom": self.nom,
            "desc": self.desc,

            "min_rp_annuels": self.min_rp_annuels,
            "min_rp_dimanches": self.min_rp_dimanches,
            "min_rpsd": self.min_rpsd,
            "min_rp_2plus": self.min_rp_2plus,
            "min_rp_semestre": self.min_rp_semestre,

            "avg_service_minutes": self.avg_service_minutes,
            "avg_tolerance_minutes": self.avg_tolerance_minutes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Regime:
        return cls(
            id=data["id"],
            nom=data["nom"],
            desc=data.get("desc") or "",

            min_rp_annuels=data.get("min_rp_annuels"),
            min_rp_dimanches=data.get("min_rp_dimanches"),
            min_rpsd=data.get("min_rpsd"),
            min_rp_2plus=data.get("min_rp_2plus"),
            min_rp_semestre=data.get("min_rp_semestre"),

            avg_service_minutes=data.get("avg_service_minutes"),
            avg_tolerance_minutes=data.get("avg_tolerance_minutes"),
        )
