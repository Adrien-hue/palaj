# app/views/database_view.py
from rich.console import Console
from rich.table import Table
from rich import box

from db.repositories import (
    agent_repo,
    poste_repo,
    regime_repo,
    tranche_repo,
    affectation_repo,
    etat_jour_agent_repo,
    qualification_repo,
)

console = Console()

class DatabaseView:
    """
    Vue console pour inspection rapide de la base.
    Utilise les repositories (singletons) exposés par db.repositories.
    """

    def __init__(self):
        # Rien à instancier : on utilise les singletons importés ci-dessus.
        pass

    # ---------- helpers ----------
    def _display_table_preview(self, title: str, headers: list[str], rows: list[list[str]], total: int):
        table = Table(title=f"📘 {title} ({total} enregistrements)", box=box.MINIMAL_DOUBLE_HEAD)
        for h in headers:
            table.add_column(h, style="cyan", no_wrap=True)
        for row in rows[:5]:
            table.add_row(*[str(x) if x is not None else "—" for x in row])
        console.print(table)

    # ---------- vues par table ----------
    def show_agents(self):
        agents = agent_repo.list_all(eager_relations=["regime"])
        total = len(agents)
        rows = [[a.id, a.nom, a.prenom, (a.regime.nom if getattr(a, "regime", None) else "—")] for a in agents]
        self._display_table_preview("Agents", ["ID", "Nom", "Prénom", "Régime"], rows, total)

    def show_postes(self):
        postes = poste_repo.list_all(eager_relations=["tranches"])
        total = len(postes)
        rows = [[p.id, p.nom] for p in postes]
        self._display_table_preview("Postes", ["ID", "Nom"], rows, total)

    def show_regimes(self):
        regimes = regime_repo.list_all()
        total = len(regimes)
        rows = [[r.id, r.nom, (r.desc or "—"), f"{r.duree_moyenne_journee_service_min} min"] for r in regimes]
        self._display_table_preview("Régimes", ["ID", "Nom", "Description", "Durée (min)"], rows, total)

    def show_tranches(self):
        tranches = tranche_repo.list_all(eager_relations=["poste"])
        total = len(tranches)
        rows = [[t.id, t.nom, t.heure_debut, t.heure_fin, (t.poste.nom if getattr(t, "poste", None) else "—")] for t in tranches]
        self._display_table_preview("Tranches", ["ID", "Nom", "Début", "Fin", "Poste"], rows, total)

    def show_affectations(self):
        total = affectation_repo.count()
        console.print(f"📊 [bold cyan]Affectations[/bold cyan] → {total} enregistrements")

    def show_etats_jour_agent(self):
        total = etat_jour_agent_repo.count()
        console.print(f"📊 [bold cyan]États journaliers agents[/bold cyan] → {total} enregistrements")

    def show_qualifications(self):
        total = qualification_repo.count()
        console.print(f"📊 [bold cyan]Qualifications[/bold cyan] → {total} enregistrements")

    # ---------- vue d’ensemble ----------
    def show_summary(self):
        console.rule("[bold yellow]Résumé de la base de données")
        self.show_agents()
        self.show_postes()
        self.show_regimes()
        self.show_tranches()
        console.rule("[bold yellow]Comptages rapides")
        self.show_affectations()
        self.show_etats_jour_agent()
        self.show_qualifications()
