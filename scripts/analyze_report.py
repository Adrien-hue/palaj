# scripts/analyze_reports.py
from core.reports.rh_analysis_report import load_reports, print_rh_summary, get_agent_report

def main():
    reports = load_reports("data/reports/report_2025.json")

    # Affiche un résumé global
    print_rh_summary(reports)

    # Exemple d’analyse ciblée
    agent_name = "Julien ALENGRIN"
    report = get_agent_report(reports, agent_name)
    if report:
        print(f"\n📋 Détail du rapport pour {agent_name}:")
        for alert in report["alerts"]:
            jour = alert.get("jour") or "—"
            print(f" {alert['severity'].upper():<8} {jour}: {alert['message']} ({alert['source']})")
    else:
        print(f"\n[WARNING] Aucun rapport trouvé pour {agent_name}")


if __name__ == "__main__":
    main()
