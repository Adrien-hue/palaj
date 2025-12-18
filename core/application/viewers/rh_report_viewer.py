# core/application/viewers/rh_report_viewer.py

from datetime import date
from typing import Dict, List

from core.utils.domain_alert import DomainAlert, Severity


class RHReportViewer:
    """
    Affichage console du résultat d'une analyse RH.
    Travaille uniquement à partir de la liste de DomainAlert retournée
    par le RHRulesEngine.
    """

    # Couleurs ANSI (alignées avec AgentPlanningViewer)
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"

    def print_grouped_by_rule(
        self,
        is_valid: bool,
        alerts: List[DomainAlert],
        level: str = "info",
    ) -> None:
        """
        Affiche un rapport RH groupé par règle (source).

        Paramètres
        ----------
        is_valid : bool
            Résultat global renvoyé par le RHRulesEngine.
        alerts : List[DomainAlert]
            Liste complète des alertes.
        level : str
            Niveau minimal de gravité à afficher :
              - "info"    → INFO + WARNING + ERROR
              - "warning" → WARNING + ERROR
              - "error"   → ERROR uniquement
        """

        level = (level or "info").lower()
        if level not in ("info", "warning", "error"):
            level = "info"

        # Ordre / poids des gravités
        severity_order = {
            Severity.ERROR: 0,
            Severity.WARNING: 1,
            Severity.INFO: 2,
        }

        # Seuil en fonction du niveau demandé
        threshold_by_level = {
            "error": Severity.ERROR,
            "warning": Severity.WARNING,
            "info": Severity.INFO,
        }
        threshold = threshold_by_level[level]

        # On ne garde que les alertes dont la gravité est >= seuil demandé
        # (ERROR < WARNING < INFO dans severity_order → plus petit = plus grave)
        filtered_alerts = [
            a
            for a in alerts
            if severity_order.get(a.severity, 99)
            <= severity_order[threshold]
        ]

        print(f"\n{self.BOLD}{self.CYAN}===== RAPPORT GLOBAL RÈGLES RH ====={self.RESET}")
        print(f"Niveau d'affichage : {level.upper()}")

        if not alerts:
            print("Aucune alerte générée.")
            print(f"{self.CYAN}===================================={self.RESET}\n")
            return

        # Résultat global (indépendant du filtrage d'affichage)
        if is_valid:
            print(f"{self.GREEN}Aucune erreur bloquante détectée.{self.RESET}")
        else:
            print(f"{self.RED}Des non-conformités ont été détectées :{self.RESET}")

        if not filtered_alerts:
            print(
                f"Aucune alerte à afficher pour ce niveau de gravité "
                f"(min = {threshold.name})."
            )
            print(f"{self.CYAN}===================================={self.RESET}\n")
            return

        # --- 1) Regroupement par règle (source) ---
        grouped: Dict[str, List[DomainAlert]] = {}
        for a in filtered_alerts:
            rule_name = a.source or "Règle inconnue"
            grouped.setdefault(rule_name, []).append(a)

        color_by_severity = {
            Severity.ERROR: self.RED,
            Severity.WARNING: self.YELLOW,
            Severity.INFO: self.GREEN,
        }

        # --- 2) Affichage groupe par groupe ---
        for rule_name in sorted(grouped.keys()):
            rule_alerts = grouped[rule_name]

            print(f"\n{self.BOLD}=== {rule_name} ==={self.RESET}")

            # Tri : gravité, date, code
            rule_alerts_sorted = sorted(
                rule_alerts,
                key=lambda a: (
                    severity_order.get(a.severity, 99),
                    a.jour or date.min,
                    a.code or "",
                ),
            )

            for a in rule_alerts_sorted:
                color = color_by_severity.get(a.severity, self.GRAY)

                prefix = {
                    Severity.INFO: "[INFO]",
                    Severity.WARNING: "[WARN]",
                    Severity.ERROR: "[ERROR]",
                }.get(a.severity, "[UNK]")

                jour_str = f"{a.jour}" if a.jour else "-"
                code_str = f" · {a.code}" if getattr(a, "code", None) else ""

                # Ligne d’en-tête (avec couleur sur la gravité)
                print(f"{color}{prefix}{self.RESET} {self.GRAY}{jour_str}{self.RESET}{code_str}")
                # Corps du message
                print(f"  {a.message}")

        print(f"\n{self.CYAN}===================================={self.RESET}\n")
