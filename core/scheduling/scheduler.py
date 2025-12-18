from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from ortools.sat.python import cp_model

from core.domain.entities import Tranche, TypeJour
from core.domain.models.poste_planning import PostePlanning

from core.application.analyzers.poste_planning_analyzer import PostePlanningAnalyzer
from core.application.services.container import agent_service, etat_jour_agent_service, poste_service, tranche_service
from core.application.viewers.poste_planning_viewer import PostePlanningViewer

from core.scheduling.availability import build_indispo_agent_ids_by_day
from core.scheduling.slot_coverage_scheduler import SlotCoverageScheduler


@dataclass(frozen=True)
class DemoAgent:
    id: int
    name: str


class DemoPlanningContext:
    pass


def make_days(start: date, nb: int):
    return [start + timedelta(days=i) for i in range(nb)]


def main():
    # Récupération des données relatives à un poste donné.
    poste_id = 4

    poste = poste_service.get_poste_complet(poste_id)

    if poste is None:
        raise ValueError(f"Impossible de récupérer le poste (id:{poste_id})")
    
    tranches = tranche_service.list_by_poste_id(poste.id)

    agents = []
    for q in poste.qualifications:
        agent = agent_service.get_agent_complet(q.agent_id)

        if agent:
            agents.append(agent)
        else:
            raise ValueError(f"Impossible de récupérer l'agent (id:{q.agent_id})")

    agents.append(agent_service.get_agent_complet(70015))

    jours = make_days(date(2025, 1, 1), 7)

    qualifications = {(q.agent_id, q.poste_id) for q in poste.qualifications}

    etats = etat_jour_agent_service.list_between_dates(min(jours), max(jours))
    etats = []
    indispo_by_day = build_indispo_agent_ids_by_day(
        etats,
        indispo_types={TypeJour.ABSENCE, TypeJour.CONGE, TypeJour.REPOS},
    )

    nb_tranches = len(tranches)

    for d in jours:
        available = 0
        for ag in agents:
            if (ag.id, poste.id) not in qualifications:
                continue
            if ag.id in indispo_by_day.get(d, set()):
                continue
            available += 1
        if available < nb_tranches:
            print(f"⚠️ {d}: qualifiés dispo={available} < tranches/jour={nb_tranches} => INFEASIBLE probable")

    scheduler = SlotCoverageScheduler(
        planning_context=DemoPlanningContext(),
        agents=agents,
        jours=jours,
        tranches=tranches,
        qualifications=qualifications,
        indispo_agent_ids_by_day=indispo_by_day,
    )
    scheduler.build_model()

    status = scheduler.solve(max_time_seconds=2.0)
    print("Status:", status,
          "OPTIMAL" if status == cp_model.OPTIMAL else
          "FEASIBLE" if status == cp_model.FEASIBLE else
          "INFEASIBLE" if status == cp_model.INFEASIBLE else
          "OTHER")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return

    affectations = scheduler.get_solution_as_affectations()
    affectations.sort(key=lambda a: (a.jour, a.tranche_id, a.agent_id))

    # agents : liste d'Agent (ou DemoAgent) avec .id
    agents_by_id = {a.id: a for a in agents}

    # tranches : liste de Tranche
    tranches_by_id = {t.id: t for t in tranches}

    poste_planning = PostePlanning.build(
        poste=poste,
        start_date=min(jours),
        end_date=max(jours),
        affectations=affectations,
        agents_by_id=agents_by_id,
        tranches_by_id=tranches_by_id,
    )

    analyzer = PostePlanningAnalyzer()
    violations = analyzer.find_unqualified_assignments(poste_planning)

    viewer = PostePlanningViewer()
    viewer.print_grid(poste_planning, violations)
    viewer.print_unqualified_summary(violations)


if __name__ == "__main__":
    main()
