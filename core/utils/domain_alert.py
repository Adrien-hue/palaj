# core/utils/domain_alert.py
from dataclasses import dataclass
from enum import Enum
from datetime import date
from typing import Optional


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class DomainAlert:
    """
    Représente une alerte ou une violation d'invariant dans le domaine.
    Peut provenir de n'importe quel service métier.
    """

    message: str
    severity: Severity = Severity.WARNING
    jour: Optional[date] = None
    source: Optional[str] = None  # ex: "AffectationService", "RHRulesService", etc.

    def __str__(self):
        color_map = {
            Severity.SUCCESS: "\033[92m ",
            Severity.INFO: "\033[94m ",
            Severity.WARNING: "\033[93m ",
            Severity.ERROR: "\033[91m ",
        }
        RESET = "\033[0m"

        prefix = f"[{self.jour}] " if self.jour else ""
        src = f"({self.source}) " if self.source else ""
        color = color_map.get(self.severity, "")

        return f"{color}{prefix}{src}{self.message}{RESET}"

    def is_error(self) -> bool:
        return self.severity == Severity.ERROR

    def is_warning(self) -> bool:
        return self.severity == Severity.WARNING
