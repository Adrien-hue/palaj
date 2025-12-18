from __future__ import annotations

from datetime import date as Date
from typing import Any, Dict, Final, List, Optional, Set, Tuple

from ortools.sat.python import cp_model

from core.domain.entities import Affectation, Agent, Tranche

from core.scheduling.slot_variable_manager import SlotVariableManager

from core.utils.profiler import profiler


class SlotCoverageScheduler:
    """
    Génère des Affectations pour couvrir des slots (jour x tranche).
    Compatible mono-poste ou groupe de postes (les tranches embarquent déjà poste_id).

    Hypothèses v1 :
      - chaque slot (jour, tranche) doit être couvert par exactement 1 agent
      - un agent ne peut faire qu'1 tranche par jour (tous postes confondus)
      - RH hard constraints (à enrichir ensuite)
    """

    def __init__(
        self,
        planning_context: Any,
        agents: List[Agent],
        jours: List[Date],
        tranches: List[Tranche],
        qualifications: Optional[Set[Tuple[int, int]]] = None,
        indispo_agent_ids_by_day: Optional[Dict[Date, Set[int]]] = None,
    ) -> None:
        self.planning_context = planning_context
        self.agents = list(agents)
        self.jours = list(jours)
        self.tranches = list(tranches)
        self.qualifications = qualifications or set()
        self.indispo_agent_ids_by_day = indispo_agent_ids_by_day or {}

        self.model = cp_model.CpModel()
        self.solver: Optional[cp_model.CpSolver] = None
        self.status: Any = None

        self.var_manager = SlotVariableManager(
            model=self.model,
            agents=self.agents,
            jours=self.jours,
            tranches=self.tranches,
        )
        self.x = {}

    @profiler.profile_call("SlotCoverageScheduler.build_model")
    def build_model(self) -> None:
        self.x = self.var_manager.create_variables()
        self._add_coverage_constraints()
        self._add_gpt_consecutive_constraints()
        self._add_one_tranche_per_day_per_agent()
        self._add_qualification_constraints()
        self._add_unavailability_constraints()

        # Objectif : minimiser la charge maximale
        self._set_objectives()
        
        # Plus tard : pénalités de changement / gel / etc.


    @profiler.profile_call("SlotCoverageScheduler._add_coverage_constraints")
    def _add_coverage_constraints(self) -> None:
        """
        Pour chaque slot s :
            somme_a x[a, s] == 1
        """
        nb_agents = len(self.agents)
        nb_slots = len(self.var_manager.slots)

        for s in range(nb_slots):
            self.model.Add(
                sum(self.var_manager.get_var(a, s) for a in range(nb_agents)) == 1
            )

    @profiler.profile_call("SlotCoverageScheduler._add_gpt_consecutive_constraints")
    def _add_gpt_consecutive_constraints(self, min_days: int = 3, max_days: int = 6, rest_after_max: int = 2) -> None:
        """
        Règle GPT :
        - toute séquence de travail (débutée dans l'horizon) dure entre min_days et max_days
        - si la séquence dure max_days (=6), alors repos rest_after_max (=2) jours juste après

        Hypothèse v1 (simple) :
        - on applique la règle aux débuts de séquence détectés DANS l'horizon.
        - si une séquence commence avant l'horizon, ce n'est pas capturé (on gèrera ça v2 via état initial).
        - si un début de séquence est trop proche de la fin pour garantir min_days, on l'interdit.
        """
        work = self._build_work_vars()

        nb_days = len(self.jours)
        nb_agents = len(self.agents)

        # start[a,i] = work[a,i] AND (i==0 or work[a,i-1]==0)
        start = {}
        for a, agent in enumerate(self.agents):
            for i, d in enumerate(self.jours):
                st = self.model.NewBoolVar(f"start_{agent.id}_{d.isoformat()}")

                if i == 0:
                    # start == work au premier jour (v1)
                    self.model.Add(st == work[(a, i)])
                else:
                    # st <= work[i]
                    self.model.Add(st <= work[(a, i)])
                    # st <= 1 - work[i-1]
                    self.model.Add(st <= 1 - work[(a, i - 1)])
                    # st >= work[i] - work[i-1]
                    self.model.Add(st >= work[(a, i)] - work[(a, i - 1)])

                start[(a, i)] = st

        # Contraintes par début de séquence
        for a in range(nb_agents):
            for i in range(nb_days):
                st = start[(a, i)]

                # --- Min 3 jours : start -> work[i+1]=1, work[i+2]=1 ---
                # Si on n'a pas assez de jours restants, on interdit le start (v1).
                if i + (min_days - 1) >= nb_days:
                    self.model.Add(st == 0)
                    continue

                for t in range(0, min_days):
                    self.model.Add(work[(a, i + t)] == 1).OnlyEnforceIf(st)

                # --- Max 6 jours : start -> work[i+6] = 0 (si dans horizon) ---
                if i + max_days < nb_days:
                    self.model.Add(work[(a, i + max_days)] == 0).OnlyEnforceIf(st)

                # --- Si séquence de 6 jours => repos 2 jours après ---
                # On crée un bool six_start[a,i] qui signifie :
                # st=1 et work[i..i+5]=1 et work[i+6]=0
                # Puis six_start -> work[i+7]=0 (2e jour repos)
                if i + max_days < nb_days:
                    # il faut i+6 dans l'horizon pour définir "exactement 6"
                    # et il faut i+7 pour imposer 2 jours de repos complets
                    if i + max_days + (rest_after_max - 1) < nb_days:
                        six = self.model.NewBoolVar(f"six_{a}_{i}")

                        # six -> st
                        self.model.Add(six <= st)

                        # six -> work[i..i+5]=1
                        for t in range(0, max_days):
                            self.model.Add(six <= work[(a, i + t)])

                        # six -> work[i+6]=0
                        self.model.Add(six <= 1 - work[(a, i + max_days)])

                        # st & allconds -> six  (approx via somme)
                        # (optionnel, mais utile pour que six puisse devenir 1)
                        self.model.Add(
                            six >= st
                            + sum(work[(a, i + t)] for t in range(0, max_days))
                            + (1 - work[(a, i + max_days)])
                            - (max_days + 1)
                        )

                        # repos 2 jours après (i+6 déjà 0 via six)
                        for r in range(0, rest_after_max):
                            self.model.Add(work[(a, i + max_days + r)] == 0).OnlyEnforceIf(six)
                    else:
                        # pas assez de jours pour garantir 2 repos après un run=6 -> on interdit cette config
                        # (sinon tu pourrais finir à J+6 sans pouvoir imposer les 2 repos dans l'horizon)
                        # => on interdit simplement de démarrer un run de 6 ici, en forçant work[i+6]=0 si st,
                        # mais sans permettre 6. La manière simple v1 : interdire st si i proche de la fin.
                        pass


    @profiler.profile_call("SlotCoverageScheduler._add_one_tranche_per_day_per_agent")
    def _add_one_tranche_per_day_per_agent(self) -> None:
        """
        Pour chaque agent a et jour d :
            somme_{slots du jour d} x[a, s] <= 1
        """
        nb_agents = len(self.agents)

        # Pré-indexation : jour -> liste d'indices s
        slots_by_day = {}
        for s, slot in enumerate(self.var_manager.slots):
            slots_by_day.setdefault(slot.jour, []).append(s)

        for a in range(nb_agents):
            for d in self.jours:
                s_list = slots_by_day.get(d, [])
                if not s_list:
                    continue
                self.model.Add(
                    sum(self.var_manager.get_var(a, s) for s in s_list) <= 1
                )

    @profiler.profile_call("SlotCoverageScheduler._add_qualification_constraints")
    def _add_qualification_constraints(self) -> None:
        """
        Interdit x[a,s] si (agent_id, poste_id) n'est pas dans self.qualifications.
        poste_id vient de la tranche du slot.
        """
        for (a, s), var in self.var_manager.iter_indexed():
            agent_id = self.agents[a].id
            poste_id = self.var_manager.slots[s].tranche.poste_id

            if (agent_id, poste_id) not in self.qualifications:
                self.model.Add(var == 0)

    @profiler.profile_call("SlotCoverageScheduler._add_unavailability_constraints")
    def _add_unavailability_constraints(self) -> None:
        """
        Si agent indispo le jour d => x[a,s] = 0 pour tous les slots de ce jour.
        """
        # index slots par jour
        slots_by_day: Dict[Date, list[int]] = {}
        for s, slot in enumerate(self.var_manager.slots):
            slots_by_day.setdefault(slot.jour, []).append(s)

        for a, agent in enumerate(self.agents):
            for d, indispos in self.indispo_agent_ids_by_day.items():
                if agent.id not in indispos:
                    continue
                for s in slots_by_day.get(d, []):
                    self.model.Add(self.var_manager.get_var(a, s) == 0)

    @profiler.profile_call("SlotCoverageScheduler._build_switch_penalties")
    def _build_switch_penalties(self) -> list[cp_model.IntVar]:
        """
        Crée des variables switch[a,i] = 1 si l'agent travaille i et i+1 et change de tranche.
        Retourne la liste des switch vars (pour l'objectif).
        """
        slot_idx = self._slot_index_by_day_and_tranche()
        tranche_ids = [t.id for t in self.tranches]

        nb_agents = len(self.agents)
        nb_days = len(self.jours)

        switches: list[cp_model.IntVar] = []

        # work[a,i] (0/1) : on peut le reconstruire simplement depuis x
        # puisqu'on a max 1 tranche/jour/agent
        work = {}
        for a, agent in enumerate(self.agents):
            for i, d in enumerate(self.jours):
                v = self.model.NewBoolVar(f"work_{agent.id}_{d.isoformat()}")
                self.model.Add(
                    v == sum(self.var_manager.get_var(a, slot_idx[(i, tid)]) for tid in tranche_ids)
                )
                work[(a, i)] = v

        for a, agent in enumerate(self.agents):
            for i in range(nb_days - 1):
                both_work = self.model.NewBoolVar(f"both_work_{agent.id}_{i}")
                # both_work <-> (work[i] AND work[i+1])
                self.model.AddBoolAnd([work[(a, i)], work[(a, i + 1)]]).OnlyEnforceIf(both_work)
                self.model.AddBoolOr([work[(a, i)].Not(), work[(a, i + 1)].Not(), both_work])

                # same = OR_t ( x[a,i,t] AND x[a,i+1,t] )
                same_terms = []
                for tid in tranche_ids:
                    and_tt = self.model.NewBoolVar(f"same_{agent.id}_{i}_{tid}")
                    s0 = slot_idx[(i, tid)]
                    s1 = slot_idx[(i + 1, tid)]
                    self.model.AddBoolAnd([self.var_manager.get_var(a, s0), self.var_manager.get_var(a, s1)]).OnlyEnforceIf(and_tt)
                    self.model.AddBoolOr([self.var_manager.get_var(a, s0).Not(), self.var_manager.get_var(a, s1).Not(), and_tt])
                    same_terms.append(and_tt)

                same = self.model.NewBoolVar(f"same_tranche_{agent.id}_{i}")
                self.model.AddMaxEquality(same, same_terms)  # same = max(and_tt)

                switch = self.model.NewBoolVar(f"switch_{agent.id}_{i}")
                # Si pas les deux jours travaillés => switch = 0
                self.model.Add(switch == 0).OnlyEnforceIf(both_work.Not())
                # Si les deux jours travaillés => switch = 1 - same
                self.model.Add(switch + same == 1).OnlyEnforceIf(both_work)

                switches.append(switch)

        return switches

    @profiler.profile_call("SlotCoverageScheduler._build_work_vars")
    def _build_work_vars(self):
        """
        work[a,i] = 1 si l'agent a travaille le jour i (tous postes/tranches confondus).
        """
        # slots_by_day : date -> [s indices]
        slots_by_day = {}
        for s, slot in enumerate(self.var_manager.slots):
            slots_by_day.setdefault(slot.jour, []).append(s)

        work = {}  # (a, i) -> BoolVar
        for a, agent in enumerate(self.agents):
            for i, d in enumerate(self.jours):
                v = self.model.NewBoolVar(f"work_{agent.id}_{d.isoformat()}")
                self.model.Add(
                    v == sum(self.var_manager.get_var(a, s) for s in slots_by_day.get(d, []))
                )
                work[(a, i)] = v

        return work

    
    @profiler.profile_call("SlotCoverageScheduler._set_objectives")
    def _set_objectives(self) -> None:
        nb_agents = len(self.agents)
        nb_slots = len(self.var_manager.slots)
        nb_days = len(self.jours)

        # -----------------------------
        # 1) Objectif actuel : max_workload
        # -----------------------------
        workloads = []
        for a in range(nb_agents):
            w = self.model.NewIntVar(0, nb_slots, f"workload_{a}")
            self.model.Add(w == sum(self.var_manager.get_var(a, s) for s in range(nb_slots)))
            workloads.append(w)

        max_w = self.model.NewIntVar(0, nb_slots, "max_workload")
        for w in workloads:
            self.model.Add(w <= max_w)

        # -----------------------------
        # 2) Pré-index : (day_index, tranche_id) -> slot_index
        # -----------------------------
        day_to_i = {d: i for i, d in enumerate(self.jours)}
        slot_idx = {}  # (i, tranche_id) -> s
        for s, slot in enumerate(self.var_manager.slots):
            i = day_to_i[slot.jour]
            slot_idx[(i, slot.tranche.id)] = s

        tranche_ids = [t.id for t in self.tranches]

        # -----------------------------
        # 3) work[a,i] = 1 si agent a travaille le jour i
        # (car max 1 tranche/jour/agent, c'est une somme de bools)
        # -----------------------------
        work = {}
        for a, agent in enumerate(self.agents):
            for i, d in enumerate(self.jours):
                v = self.model.NewBoolVar(f"work_{agent.id}_{d.isoformat()}")
                self.model.Add(
                    v == sum(self.var_manager.get_var(a, slot_idx[(i, tid)]) for tid in tranche_ids)
                )
                work[(a, i)] = v

        # -----------------------------
        # 4) switch[a,i] = 1 si work[i]=1 et work[i+1]=1 et tranche différente
        # On calcule same[a,i] = OR_t (x[a,i,t] AND x[a,i+1,t])
        # puis switch = both_work AND (NOT same)
        # -----------------------------
        switches = []

        for a, agent in enumerate(self.agents):
            for i in range(nb_days - 1):
                # both_work <-> work[i] AND work[i+1]
                both_work = self.model.NewBoolVar(f"both_work_{agent.id}_{i}")
                self.model.AddBoolAnd([work[(a, i)], work[(a, i + 1)]]).OnlyEnforceIf(both_work)
                self.model.AddBoolOr([work[(a, i)].Not(), work[(a, i + 1)].Not(), both_work])

                # same = OR_t (x[a,i,t] AND x[a,i+1,t])
                same_terms = []
                for tid in tranche_ids:
                    and_tt = self.model.NewBoolVar(f"same_{agent.id}_{i}_{tid}")
                    s0 = slot_idx[(i, tid)]
                    s1 = slot_idx[(i + 1, tid)]
                    self.model.AddBoolAnd([self.var_manager.get_var(a, s0), self.var_manager.get_var(a, s1)]).OnlyEnforceIf(and_tt)
                    self.model.AddBoolOr([self.var_manager.get_var(a, s0).Not(), self.var_manager.get_var(a, s1).Not(), and_tt])
                    same_terms.append(and_tt)

                same = self.model.NewBoolVar(f"same_tranche_{agent.id}_{i}")
                self.model.AddMaxEquality(same, same_terms)  # same = max(and_tt)

                switch = self.model.NewBoolVar(f"switch_{agent.id}_{i}")

                # Si pas les deux jours travaillés -> switch = 0
                self.model.Add(switch == 0).OnlyEnforceIf(both_work.Not())
                # Si les deux jours travaillés -> switch = 1 - same
                self.model.Add(switch + same == 1).OnlyEnforceIf(both_work)

                switches.append(switch)

        # -----------------------------
        # 5) Objectif combiné
        # BIG donne la priorité à l'équilibrage avant la stabilité de tranche
        # -----------------------------
        BIG: Final[int] = 1000
        SWITCH_W: Final[int] = 1

        # switch_cost: IntVar
        switch_cost = self.model.NewIntVar(0, len(switches), "switch_cost")
        self.model.Add(switch_cost == sum(switches))

        obj = cp_model.LinearExpr.WeightedSum([max_w, switch_cost], [BIG, SWITCH_W])
        self.model.Minimize(obj)

    @profiler.profile_call("SlotCoverageScheduler._slot_index_by_day_and_tranche")
    def _slot_index_by_day_and_tranche(self) -> dict[tuple[int, int], int]:
        """
        Retourne mapping (day_index i, tranche_id) -> slot_index s
        """
        day_to_i = {d: i for i, d in enumerate(self.jours)}
        idx = {}
        for s, slot in enumerate(self.var_manager.slots):
            i = day_to_i[slot.jour]
            idx[(i, slot.tranche.id)] = s
        return idx

    @profiler.profile_call("SlotCoverageScheduler.solve")
    def solve(self, max_time_seconds: Optional[float] = None) -> Any:
        solver = cp_model.CpSolver()
        if max_time_seconds is not None:
            solver.parameters.max_time_in_seconds = max_time_seconds

        status = solver.Solve(self.model)
        self.solver = solver
        self.status = status
        return status

    def get_solution_as_affectations(self) -> List[Affectation]:
        if self.solver is None:
            raise RuntimeError("Le modèle n'a pas encore été résolu.")
        return self.var_manager.decode_solution_as_affectations(self.solver)
