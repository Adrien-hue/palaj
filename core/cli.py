# core/cli.py
import argparse
import sys
from datetime import date
from core.reports.rh_analysis_report import (
    load_reports,
    print_rh_summary,
    get_agent_report,
)
from core.validators.agent_planning_validator import AgentPlanningValidator
from core.reports.planning_validation_report import PlanningValidationReport, VerbosityLevel
from core.rh_rules.rh_rules_engine import RHRulesEngine
from core.rh_rules.rule_amplitude_max import AmplitudeMaxRule
from core.rh_rules.rule_duree_travail import DureeTravailRule
from core.rh_rules.rule_grande_periode_travail import GrandePeriodeTravailRule
from core.rh_rules.rule_repos_double import ReposDoubleRule
from core.rh_rules.rule_repos_quotidien import ReposQuotidienRule
from core.rh_rules.rule_repos_qualifie_info import ReposQualifieInfoRule
from core.agent_planning import AgentPlanning
from db.database import JsonDatabase
from db.repositories.agent_repo import AgentRepository
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.poste_repo import PosteRepository
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.tranche_repo import TrancheRepository
import json

db = JsonDatabase()

agent_repo = AgentRepository(db)
affectation_repo = AffectationRepository(db)
etat_jour_agent_repo = EtatJourAgentRepository(db)
poste_repo = PosteRepository(db)
qualification_repo = QualificationRepository(db)
tranche_repo = TrancheRepository(db)


def run_validation(year: int, save: bool):
    """Valide le planning de tous les agents pour une année donnée."""
    rh_rules_engine = RHRulesEngine(
        [
            AmplitudeMaxRule(),
            DureeTravailRule(),
            GrandePeriodeTravailRule(),
            ReposDoubleRule(),
            ReposQuotidienRule(),
            ReposQualifieInfoRule(),
        ],
        verbose=False,
    )

    validator = AgentPlanningValidator(rh_rules_engine=rh_rules_engine)
    all_reports = []

    for agent in agent_repo.list_all():
        if not agent:
            print(f"[⚠️] Agent introuvable.")
            continue

        print(f"\n🔍 Validation du planning {year} pour {agent.get_full_name()}...")

        planning = AgentPlanning(
            agent=agent,
            start_date=date(year, 1, 1),
            end_date=date(year, 12, 31),
            affectation_repo=affectation_repo,
            etat_jour_agent_repo=etat_jour_agent_repo,
            poste_repo=poste_repo,
            qualification_repo=qualification_repo,
            tranche_repo=tranche_repo,
        )

        alerts = validator.validate(planning)
        report = PlanningValidationReport(
            agent_name=planning.agent.get_full_name(),
            alerts=alerts,
            verbose=True,
            level=VerbosityLevel.WARNING,
        )

        all_reports.append(report.export_dict())
        report.print_summary()

    if save:
        path = f"data/reports/report_{year}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(all_reports, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n✅ Rapport complet exporté vers {path}")
    else:
        print("\n💡 Simulation terminée (aucune sauvegarde effectuée).")


def run_analysis(year: int, agent_name: str | None = None):
    """Analyse les rapports existants."""
    path = f"data/reports/report_{year}.json"
    reports = load_reports(path)

    if agent_name:
        report = get_agent_report(reports, agent_name)
        if not report:
            print(f"⚠️ Aucun rapport trouvé pour {agent_name}")
            sys.exit(0)

        print(f"\n📋 Rapport détaillé pour {agent_name}:")
        for alert in report["alerts"]:
            jour = alert.get("jour") or "—"
            print(f" {alert['severity'].upper():<8} {jour}: {alert['message']} ({alert['source']})")
    else:
        print_rh_summary(reports)


def main():
    parser = argparse.ArgumentParser(
        description="Outil d'analyse et de validation RH des plannings d'agents."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Commande : validate ---
    validate_parser = subparsers.add_parser(
        "validate", help="Valide les plannings d'agents pour une année donnée."
    )
    validate_parser.add_argument(
        "--year", type=int, default=date.today().year, help="Année à valider (défaut: année courante)"
    )
    validate_parser.add_argument(
        "--save", action="store_true", help="Sauvegarde le rapport JSON final."
    )

    # --- Commande : analyze ---
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyse un rapport déjà généré."
    )
    analyze_parser.add_argument(
        "--year", type=int, default=date.today().year, help="Année du rapport à analyser (défaut: année courante)."
    )
    analyze_parser.add_argument(
        "--agent", type=str, help="Nom complet de l'agent à analyser."
    )

    args = parser.parse_args()

    if args.command == "validate":
        run_validation(args.year, args.save)
    elif args.command == "analyze":
        run_analysis(args.year, args.agent)


if __name__ == "__main__":
    main()
