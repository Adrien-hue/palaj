# core/reports/rh_analysis_report.py
import json

def get_top_agents_with_errors(reports, top_n=5):
    """Retourne les agents avec le plus d'erreurs RH."""
    sorted_reports = sorted(
        reports,
        key=lambda r: sum(1 for a in r["alerts"] if a["severity"].upper() == "ERROR"),
        reverse=True,
    )
    return sorted_reports[:top_n]


def get_agents_with_no_alerts(reports):
    """Retourne les agents sans aucune alerte."""
    return [r for r in reports if len(r["alerts"]) == 0]


def get_agent_report(reports, agent_name):
    """Retourne le rapport complet d'un agent (par nom)."""
    for r in reports:
        if r.get("summary", {}).get("agent", "").lower() == agent_name.lower():
            return r
    return None


def load_reports(path="data/reports/report_2025.json"):
    """Charge un fichier de rapports JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_rh_summary(reports):
    """Affiche un résumé global de l'analyse RH."""
    print("\n🔴 Top 5 des agents avec le plus d'erreurs RH :")
    for r in get_top_agents_with_errors(reports, 5):
        nb_errors = sum(1 for a in r["alerts"] if a["severity"].upper() == "ERROR")
        print(f" - {r['summary']['agent']}: {nb_errors} erreurs ({len(r['alerts'])} alertes totales)")

    no_alerts = get_agents_with_no_alerts(reports)
    print(f"\n🟢 {len(no_alerts)} agents sans aucune non-conformité :")
    for r in no_alerts:
        print(f" - {r['summary']['agent']}")
