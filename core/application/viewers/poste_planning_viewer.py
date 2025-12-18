# core/application/viewers/poste_planning_viewer.py

from __future__ import annotations

from typing import Any, List, Optional

from core.application.analyzers.poste_planning_analyzer import UnqualifiedAssignment
from core.domain.models.poste_planning import PostePlanning


class PostePlanningViewer:
    """
    Affichage console du planning d'un poste.

    Attendu sur `planning` (PostePlanning) :
      - planning.poste (avec .nom ou __str__)
      - planning.start_date / planning.end_date
      - planning.dates : List[date]
      - planning.tranches : List[Tranche] (avec .nom et .id)
      - planning.get_agent_for(jour: date, tranche: Tranche) -> Agent | None
      - (optionnel) planning.get_uncovered_slots() -> List[(date, Tranche)]
    """

    # Couleurs ANSI
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"

    # ---------------------------------------------------------
    # 1) Vue Grille
    # ---------------------------------------------------------
    def print_grid(self, planning: PostePlanning, unqualified: List[UnqualifiedAssignment] | None = None,) -> None:
        unqualified = unqualified or []

        # Index pour lookup O(1)
        unqualified_index = {
            (u.jour, u.tranche_id): u
            for u in unqualified
        }

        poste = getattr(planning, "poste", None)
        poste_name = getattr(poste, "nom", None) or (str(poste) if poste else "Poste ?")

        print(f"\n{self.BOLD}{self.CYAN}Planning du poste : {poste_name}{self.RESET}")
        print(f"Période : {planning.start_date} → {planning.end_date}")
        print("-" * 100)

        tranches = list(planning.tranches)
        if not tranches:
            print(f"{self.RED}Aucune tranche pour ce poste.{self.RESET}")
            return

        # Noms des colonnes
        tranche_names = [getattr(t, "nom", str(t)) for t in tranches]

        # Largeurs
        date_col_w = 12  # "lun 01/12"
        col_w = self._compute_col_width(planning, tranches, tranche_names, min_w=10, max_w=20)

        # En-tête
        header = f"{self.BOLD}{'Date'.ljust(date_col_w)}{self.RESET} "
        for n in tranche_names:
            header += f"{self.BOLD}{n[:col_w].ljust(col_w)}{self.RESET} "
        print(header)

        print("-" * (date_col_w + 1 + (col_w + 1) * len(tranches)))

        # Lignes
        for jour in planning.dates:
            jour_str = jour.strftime("%a %d/%m")
            row = f"{self.GRAY}{jour_str.ljust(date_col_w)}{self.RESET} "

            for tranche in tranches:
                agent = planning.get_agent_for(jour, tranche)

                violation = unqualified_index.get(
                    (jour, tranche.id)
                )

                cell = self._format_agent(agent, col_w, violation=violation)
                row += cell + " "
            print(row)

        # Petit résumé couverture
        self._print_coverage_summary(planning)

    # ---------------------------------------------------------
    # 2) Vue Détail (jour -> tranches)
    # ---------------------------------------------------------
    def print_detailed(self, planning: Any) -> None:
        poste = getattr(planning, "poste", None)
        poste_name = getattr(poste, "nom", None) or (str(poste) if poste else "Poste ?")

        print(f"\n{self.BOLD}{self.CYAN}Planning détaillé du poste : {poste_name}{self.RESET}")
        print(f"Période : {planning.start_date} → {planning.end_date}")
        print("-" * 80)

        tranches = list(planning.tranches)
        if not tranches:
            print(f"{self.RED}Aucune tranche pour ce poste.{self.RESET}")
            return

        for jour in planning.dates:
            jour_str = jour.strftime("%A %d/%m/%Y")
            print(f"\n{self.BOLD}{self.GRAY}{jour_str}{self.RESET}")

            for tranche in tranches:
                tranche_name = getattr(tranche, "nom", str(tranche))
                agent = planning.get_agent_for(jour, tranche)

                if agent is None:
                    print(f"  - {tranche_name} : {self.RED}Non couvert{self.RESET}")
                else:
                    print(f"  - {tranche_name} : {self.GREEN}{agent.get_full_name()}{self.RESET}")

        self._print_coverage_summary(planning)

    def print_unqualified_summary(self, violations: List[UnqualifiedAssignment]) -> None:
        if not violations:
            print(f"\n{self.GREEN}OK : aucun agent hors-qualification sur ce poste.{self.RESET}")
            return

        print(f"\n{self.RED}{self.BOLD}Agents affectés hors-qualification ({len(violations)}){self.RESET}")
        for v in violations[:20]:
            print(f" - {v.jour} | {v.tranche_name} | {v.agent_label} (agent_id={v.agent_id})")
        if len(violations) > 20:
            print(f" ... +{len(violations) - 20} autres")

    def _format_agent(self, agent: Optional[Any], width: int, violation: Optional[UnqualifiedAssignment] = None) -> str:
        if agent is None:
            return f"{self.RED}{'—'.ljust(width)}{self.RESET}"

        label = agent.get_full_name()
        txt = label[:width].ljust(width)

        if violation is not None:
            return f"{self.RED}{txt}{self.RESET}"

        return f"{self.GREEN}{txt}{self.RESET}"

    def _compute_col_width(
        self,
        planning: Any,
        tranches: List[Any],
        tranche_names: List[str],
        min_w: int = 10,
        max_w: int = 20,
    ) -> int:
        # Base : le plus long nom de tranche
        base = max(len(n) for n in tranche_names)

        # On essaie d’estimer le plus long label agent sur la période (pour éviter une grille illisible)
        longest_agent = 0
        for jour in planning.dates:
            for tranche in tranches:
                agent = planning.get_agent_for(jour, tranche)
                if agent is not None:
                    longest_agent = max(longest_agent, len(agent.get_full_name()))

        w = max(base, longest_agent, min_w)
        return min(w, max_w)

    def _print_coverage_summary(self, planning: Any) -> None:
        # Si ton PostePlanning expose get_uncovered_slots() c'est parfait
        if hasattr(planning, "get_uncovered_slots"):
            uncovered = planning.get_uncovered_slots()
            total_slots = len(planning.dates) * len(planning.tranches)
            covered = total_slots - len(uncovered)

            pct = 0.0 if total_slots == 0 else round(100 * covered / total_slots, 1)

            print("\n" + "-" * 60)
            print(
                f"{self.GRAY}Couverture :{self.RESET} "
                f"{self.GREEN}{covered}{self.RESET}/{total_slots} "
                f"({self.YELLOW}{pct}%{self.RESET})"
            )

            if uncovered:
                # Affiche juste un échantillon pour ne pas spammer
                sample = uncovered[:10]
                print(f"{self.RED}Non couverts (extrait) :{self.RESET}")
                for (jour, tranche) in sample:
                    tname = getattr(tranche, "nom", str(tranche))
                    print(f"  - {jour} / {tname}")
                if len(uncovered) > 10:
                    print(f"  ... +{len(uncovered) - 10} autres")
            print("-" * 60)
