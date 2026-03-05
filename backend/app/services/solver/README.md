# Solver OR-Tools (backend/app/services/solver)

## CI note

Validation ciblée solver :

```bash
pytest -q tests/backend/services/solver/test_ortools_solver.py
```

## v3 stats payload (breaking)

Le payload `PlanningGenerateStatusResponse.result_stats` est désormais strict et minimal :

- `result_stats.result_stats_schema_version = 3`
- `result_stats.stats` contient uniquement les familles groupées (`meta`, `timing`, `model`, `coverage`, `objective`, `solution_quality`, `lns`, `cp_sat`)
- toutes les anciennes clés flat legacy à la racine de `result_stats` ont été supprimées

Canonical sources :

- objectifs/score : `stats.objective`
- couverture/sous-effectif : `stats.coverage`
- itérations LNS : `stats.lns.iteration_history` (unique liste d'historique)
- détails phases CP-SAT : `stats.cp_sat.phases`
- trace CP-SAT : `stats.cp_sat.best_objective_over_time_points` (+ `time_to_first_feasible_seconds` dans `stats.cp_sat`)

Verbosity/troncature :

- priorité: `PLANNING_STATS_VERBOSITY`, sinon `PLANNING_STATS_DEFAULT_VERBOSITY`, sinon `debug`
- en `compact`, les listes lourdes restent des listes mais sont tronquées avec métadonnées
  `*_truncated` et `*_total` (modèle, couverture, historique LNS)
