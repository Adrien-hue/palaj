# core/application/diagnostics/data_integrity_report.py

from typing import Dict, List
from core.utils.domain_alert import DomainAlert


class DataIntegrityReport:
    """
    Responsable UNIQUEMENT d'afficher
    ou formater un rapport d'intégrité.
    """

    def __init__(self, results: Dict[str, List[DomainAlert]]):
        self.results = results

    def print_report(self):
        """Affiche un rapport console lisible et coloré."""
        BOLD = "\033[1m"
        RESET = "\033[0m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        GRAY = "\033[90m"
        GREEN = "\033[92m"

        errors = self.results["errors"]
        warnings = self.results["warnings"]
        infos = self.results["infos"]

        print(f"\n{CYAN}{BOLD}=== Rapport d'intégrité des données ==={RESET}\n")

        if not errors and not warnings:
            print(f"{GREEN}Aucune anomalie détectée !{RESET}")
            return

        if errors:
            print(f"{RED}{BOLD}Erreurs critiques :{RESET}")
            for e in errors:
                print(f"  - {e.message} ({e.source})")
            print()

        if warnings:
            print(f"{YELLOW}{BOLD}Avertissements :{RESET}")
            for w in warnings:
                print(f"  - {w.message} ({w.source})")
            print()

        if infos:
            print(f"{GRAY}{BOLD}Informations :{RESET}")
            for i in infos:
                print(f"  - {i.message} ({i.source})")
            print()

        print(f"\n{CYAN}--- Fin du rapport ---{RESET}\n")
