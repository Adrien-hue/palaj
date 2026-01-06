# core/utils/domain_alert.py
from dataclasses import dataclass
from datetime import date
from typing import Optional
import textwrap

from core.utils.severity import Severity

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
    code: Optional[str] = None

    # === Options d'affichage (faciles à ajuster) ===
    USE_COLORS: bool = True
    INDENT_MESSAGE: str = "  "  # indentation pour le corps du message

    def __str__(self) -> str:
        # Palette de couleurs simple (ANSI)
        if self.USE_COLORS:
            COLOR_MAP = {
                Severity.SUCCESS: "\033[92m",  # vert
                Severity.INFO:    "\033[94m",  # bleu
                Severity.WARNING: "\033[93m",  # jaune
                Severity.ERROR:   "\033[91m",  # rouge
            }
            BOLD = "\033[1m"
            RESET = "\033[0m"
        else:
            COLOR_MAP = {s: "" for s in Severity}
            BOLD = ""
            RESET = ""

        color = COLOR_MAP.get(self.severity, "")
        severity_label = self.severity.value.upper()

        # Ligne d'en-tête (métadonnées)
        meta_parts = []
        if self.jour:
            meta_parts.append(self.jour.isoformat())
        if self.source:
            meta_parts.append(self.source)
        if self.code:
            meta_parts.append(self.code)

        meta_str = " · ".join(meta_parts)

        if meta_str:
            header = f"{color}{BOLD}[{severity_label}]{RESET} {meta_str}"
        else:
            header = f"{color}{BOLD}[{severity_label}]{RESET}"

        # Corps du message, éventuellement multi-ligne, avec indentation
        wrapped_message = textwrap.fill(
            self.message,
            width=100,
            subsequent_indent=self.INDENT_MESSAGE,
        )
        body = f"{self.INDENT_MESSAGE}{wrapped_message}"

        return f"{header}\n{body}"

    def is_error(self) -> bool:
        return self.severity == Severity.ERROR

    def is_warning(self) -> bool:
        return self.severity == Severity.WARNING

    def is_info(self) -> bool:
        return self.severity == Severity.INFO
