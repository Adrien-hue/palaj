from datetime import date
from enum import Enum, IntEnum
from typing import List, Dict
import json

from core.utils.domain_alert import DomainAlert, Severity


class VerbosityLevel(IntEnum):
    """Niveau de détail du rapport (inspiré de logging)."""
    ERROR = 40
    WARNING = 30
    INFO = 20
    ALL = 10


class ValidationStatus(Enum):
    OK = 1
    WARNING = 2
    ERROR = 3

    def label(self) -> str:
        return {
            ValidationStatus.OK: "Conforme",
            ValidationStatus.WARNING: "Avertissements",
            ValidationStatus.ERROR: "Non conforme",
        }[self]


class PlanningValidationReport:
    """
    Rapport complet de validation RH d’un planning agent.
    Permet de filtrer les alertes selon un niveau de verbosité.
    """

    COLORS = {
        Severity.INFO: "\033[94m",     # Bleu clair
        Severity.WARNING: "\033[93m",  # Jaune
        Severity.ERROR: "\033[91m",    # Rouge
        Severity.SUCCESS: "\033[92m",  # Vert
    }
    RESET = "\033[0m"

    SEVERITY_TO_LEVEL = {
        Severity.ERROR: VerbosityLevel.ERROR,
        Severity.WARNING: VerbosityLevel.WARNING,
        Severity.INFO: VerbosityLevel.INFO,
        Severity.SUCCESS: VerbosityLevel.ALL,
    }

    def __init__(
        self,
        agent_name: str,
        alerts: List[DomainAlert],
        verbose: bool = False,
        level: VerbosityLevel = VerbosityLevel.INFO,  # 👈 nouveau paramètre
    ):
        self.agent_name = agent_name
        self.alerts = alerts
        self.verbose = verbose
        self.level = level

    # ------------------------------------------------------------
    def _filter_alerts(self, alerts: List[DomainAlert]) -> List[DomainAlert]:
        """Filtre les alertes selon le niveau de verbosité choisi."""
        return [
            a for a in alerts
            if self.SEVERITY_TO_LEVEL.get(a.severity, VerbosityLevel.ALL) >= self.level
        ]

    # ------------------------------------------------------------
    def summary(self) -> Dict[str, str | int | ValidationStatus]:
        total = len(self.alerts)
        errors = sum(1 for a in self.alerts if a.severity == Severity.ERROR)
        warnings = sum(1 for a in self.alerts if a.severity == Severity.WARNING)
        infos = sum(1 for a in self.alerts if a.severity == Severity.INFO)

        if errors > 0:
            status = ValidationStatus.ERROR
        elif warnings > 0:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.OK

        return {
            "agent": self.agent_name,
            "total_alerts": total,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
            "status": status,
        }

    # ------------------------------------------------------------
    def print_summary(self):
        summary = self.summary()
        status = summary["status"]

        print(f"\nValidation du planning de {summary['agent']}")
        print("─" * 60)

        if type(status) is not ValidationStatus:
            raise TypeError("Le statut doit être un ValidationStatus")
        
        color = {
            ValidationStatus.OK: self.COLORS[Severity.SUCCESS],
            ValidationStatus.WARNING: self.COLORS[Severity.WARNING],
            ValidationStatus.ERROR: self.COLORS[Severity.ERROR],
        }[status]

        print(f"{color}{status.label()}{self.RESET}")
        print(
            f"Alertes : {summary['total_alerts']} "
            f"(Erreurs {summary['errors']} | Avertissements {summary['warnings']} | Infos {summary['infos']})"
        )

        if self.verbose:
            self.print_detailed()

    def print_detailed(self, sort_by_date: bool = True):
        """Affiche les alertes selon le niveau de verbosité configuré."""
        filtered_alerts = self._filter_alerts(self.alerts)

        if not filtered_alerts:
            print(f"{self.COLORS[Severity.SUCCESS]}✅ Aucune anomalie détectée.{self.RESET}")
            return

        print("\nDétails des alertes :")
        print("─" * 60)

        alerts = sorted(filtered_alerts, key=lambda a: (a.jour or date.min)) if sort_by_date else filtered_alerts

        for a in alerts:
            color = self.COLORS.get(a.severity, "")
            date_str = a.jour.strftime("%Y-%m-%d") if a.jour else "—"
            print(f"{color}[{date_str}] {a.severity.name:<8} {a.message}{self.RESET}")
            if a.source:
                print(f"    ↳ Source : {a.source}")

    # ------------------------------------------------------------
    def export_dict(self) -> Dict:
        filtered_alerts = self._filter_alerts(self.alerts)
        return {
            "summary": self.summary(),
            "alerts": [
                {
                    "date": a.jour.isoformat() if a.jour else None,
                    "severity": a.severity.name,
                    "message": a.message,
                    "source": a.source,
                }
                for a in filtered_alerts
            ],
        }

    def export_json(self) -> str:
        return json.dumps(self.export_dict(), indent=2, ensure_ascii=False)
