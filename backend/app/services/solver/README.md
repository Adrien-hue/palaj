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
- caps centralisés dans `backend/app/services/solver/constants.py::STATS_PAYLOAD_CAPS`
- `StatsCollector` est l'unique endroit où les caps/troncatures sont appliqués (pas de trimming côté solver/phases/LNS)
- en `debug`, les champs lourds sont conservés mais capés (hard-caps) pour éviter des payloads trop volumineux
- en `compact`, les champs lourds sont plus agressivement capés
- types stables: une liste reste une liste, un dict reste un dict
- chaque champ lourd expose des métadonnées cohérentes:
  - `<field>_total` = taille originale avant cap
  - `<field>_truncated` = bool (`True` si cap appliqué)
- `stats.coverage.understaff_by_day_weighted`:
  - `debug`: garde la fenêtre complète (valeurs à 0 incluses), avec cap de sécurité
  - `compact`: ne garde que les jours > 0 puis applique le cap
- `stats.lns.iteration_history` est slimmé (champs canoniques uniquement) puis capé selon la verbosité.
  Schéma slim: `t`, `poste_id`, `selected_postes`, `relaxed_days_count`, `fixed_y_count`,
  `relaxed_y_count`, `neighborhood_mode_effective`, `solve_wall_time_seconds_iter`,
  `accepted`, `status_raw`, `status_int`, `validate_message_present`,
  `understaff_total_unweighted`, `objective_value`
- `stats.cp_sat.best_objective_over_time_points` est capé selon la verbosité avec métadonnées associées

## v3 invariants

- `StatsCollector` est l'unique endroit où les caps/troncatures sont appliqués.
- `stats.coverage.understaff_by_day_weighted` en `debug` contient tous les jours de la fenêtre (zéros inclus).
- règle uniforme de métadonnées:
  - `<field>_total` = nombre d'entrées avant cap
  - `<field>_truncated` = cap appliqué (`True`) ou non (`False`)
- `stats.lns.iteration_history` suit le schéma slim suivant uniquement:
  `t`, `poste_id`, `selected_postes`, `relaxed_days_count`, `neighborhood_mode_effective`,
  `solve_wall_time_seconds_iter`, `accepted`, `status_raw`, `status_int`, `objective_value`,
  `understaff_total_unweighted`, `fixed_y_count`, `relaxed_y_count`, `validate_message_present`.
