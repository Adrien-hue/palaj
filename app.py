# import argparse
# from datetime import date
# from rich.console import Console
# from rich.table import Table
# from rich.panel import Panel

# from core.application.diagnostics.data_integrity_checker import DataIntegrityChecker
# from core.application.diagnostics.data_integrity_report import DataIntegrityReport

# from core.application.config.rh_rules_config import build_default_rh_engine
# from core.application.services import AgentPlanningValidatorService

# from core.application.viewers.agent_planning_viewer import AgentPlanningViewer
# from core.application.viewers.poste_planning_viewer import PostePlanningViewer
# from core.application.viewers.rh_report_viewer import RHReportViewer

# from core.features.database_view import DatabaseView

# console = Console()

# def main_menu():
#     while True:
#         console.print("\n=== MENU PRINCIPAL ===")
#         console.print("1 - Afficher la base (summary)")
#         console.print("2 - Vérifier l'intégrité des données")
#         console.print("3 - Afficher le planning...")
#         console.print("4 - Analyse RH du planning d'un agent")
#         console.print("0 - Quitter\n")

#         choice = console.input("→ Votre choix : ")

#         if choice == "1":
#             DatabaseView().show_summary()
#         elif choice == "2":
#             checker = DataIntegrityChecker()
            
#             dict_res = checker.run_all_checks()
            
#             reporter = DataIntegrityReport(dict_res)
            
#             reporter.print_report()
#         elif choice == "3":
#             show_planning()
#         elif choice == "4":
#             run_rh_validation()
#         elif choice == "0":
#             break

# def ask_date(prompt: str) -> date:
#     while True:
#         value = input(prompt + " (format YYYY-MM-DD) : ").strip()
#         try:
#             return date.fromisoformat(value)
#         except ValueError:
#             print("❌ Format invalide. Exemple valide : 2025-01-15")

# def ask_agent():
#     agents = agent_service.list_all()

#     print("\n👤 Liste des agents :")
#     for ag in agents:
#         print(f"{ag.id} — {ag.get_full_name()}")

#     while True:
#         try:
#             aid = int(input("\nID de l'agent à visualiser : "))
#             ag = agent_service.get(aid)
#             if ag:
#                 return ag.id
#             print("❌ Agent introuvable.")
#         except ValueError:
#             print("❌ Veuillez saisir un nombre.")

# def ask_poste():
#     postes = poste_service.list_all()

#     print("\n🏢 Liste des postes :")
#     for p in postes:
#         print(f"{p.id} — {p.nom}")

#     while True:
#         try:
#             pid = int(input("\nID du poste à visualiser : "))
#             p = poste_service.get(pid)
#             if p:
#                 return p.id
#             print("❌ Poste introuvable.")
#         except ValueError:
#             print("❌ Veuillez saisir un nombre.")

# def show_planning():
#     print("\n=== 🗓️ Afficher un planning ===")
#     print("1 - Planning agent")
#     print("2 - Planning poste")

#     sub = input("→ Votre choix : ").strip()

#     if sub == "1":
#         show_agent_planning()
#     elif sub == "2":
#         show_poste_planning()
#     else:
#         print("❌ Choix invalide.")

# def show_agent_planning():
#     print("\n=== 🗓️ Visualisation d'un planning agent ===")

#     agent_id = ask_agent()
#     start = ask_date("Date de début")
#     end = ask_date("Date de fin")

#     if start > end:
#         print("❌ La date de début doit être ≤ date de fin.")
#         return

#     # Construction du planning
#     planning = planning_builder_service.build_agent_planning(
#         agent_id=agent_id,
#         start_date=start,
#         end_date=end
#     )

#     # Affichage
#     viewer = AgentPlanningViewer()
#     viewer.print_detailed(planning)
#     viewer.summary(planning)

# def show_poste_planning():
#     print("\n=== 🗓️ Visualisation d'un planning poste ===")

#     poste_id = ask_poste()
#     start = ask_date("Date de début")
#     end = ask_date("Date de fin")

#     if start > end:
#         print("❌ La date de début doit être ≤ date de fin.")
#         return

#     planning = planning_builder_service.build_poste_planning(
#         poste_id=poste_id,
#         start_date=start,
#         end_date=end
#     )

#     viewer = PostePlanningViewer()
#     viewer.print_grid(planning)
#     # viewer.print_detailed(planning)  # si tu veux une vue jour par jour

# def run_rh_validation():
#     print("\n=== Analyse RH du planning d'un agent ===")

#     agent_id = ask_agent()
#     start = ask_date("Date de début")
#     end = ask_date("Date de fin")

#     # --- Construction du planning ---
    
#     planning = planning_builder_service.build_agent_planning(
#         agent_id=agent_id,
#         start_date=start,
#         end_date=end
#     )

#     # --- Validation RH ---
#     rh_engine = build_default_rh_engine()
#     agent_planning_validator_service = AgentPlanningValidatorService(rh_engine)
#     ok, alerts = agent_planning_validator_service.validate(planning)

#     # --- Affichage des résultats ---
#     viewer = RHReportViewer()
#     viewer.print_grouped_by_rule(ok, alerts, level="warning")


# def main():
#     parser = argparse.ArgumentParser(description="Application RH - Mode console / API")
#     parser.add_argument("--init-db", action="store_true", help="Crée le schéma de base")
#     parser.add_argument("--menu", action="store_true", help="Lance l'interface console")
#     parser.add_argument("--demo", type=int, help="Analyse RH pour un agent donné")

#     args = parser.parse_args()

#     if args.init_db:
#         pass
#         # init_database()
#     elif args.menu:
#         main_menu()
#     else:
#         parser.print_help()


# if __name__ == "__main__":
#     main()
# exit()