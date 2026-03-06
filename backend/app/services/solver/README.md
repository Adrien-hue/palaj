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

## Existing assignments invariants

- La source de vérité prioritaire est `existing_daytype_by_agent_day_ctx` (DB). En cas de conflit avec `absences` solver, la résolution reste déterministe et auditée (`existing_assignments_conflicts_count`, `existing_assignments_conflicts_sample`).
- Les pénalités de changement d'existant (`existing_change_strong_total`, `existing_change_medium_total`) ne s'appliquent **que** aux jours dans la fenêtre de planification (in-window), jamais aux jours de contexte hors fenêtre.
- Pour `WORKING`, la signature connue est `(poste_id, tranche_ids triés)`. Si la signature DB ne matche aucun combo, le solveur ne crash pas: il applique les règles de pénalité WORKING, et alimente `existing_working_signature_unknown_count` + `existing_working_signature_unknown_sample`.
- Si la DB indique `WORKING` mais sans assignment exploitable (`tranche_ids` manquant/vide), le jour est audité via `existing_working_missing_assignments_count_total` + `existing_working_missing_assignments_sample` (max 10), et ne peut pas contribuer à un intervalle de service pour la règle RPDOUBLE.

- Pas de trimming côté solver pour ces audits; les caps payload restent centralisés dans `StatsCollector`.

## Règle GPT "repos double" (RPDOUBLE) — gap temporel 60h20

La règle RPDOUBLE n'est **pas** "2 jours off".

- Après une séquence de **6 jours travaillés consécutifs** (jour `worked=1`), le prochain jour travaillé doit respecter un écart minimal de **3620 minutes**.
- Formulation: `next_start_abs >= last_end_abs + 3620`.

Définitions de modélisation:

- Un jour est `worked=1` uniquement si un combo avec intervalle de service (tranches non vides) est choisi.
- `REST`, `ZCOT` sans tranche, `LEAVE`, `ABSENT` sont `worked=0` pour cette règle.
- Le calcul se fait sur toute la timeline de contexte (`context_days`), pas seulement la fenêtre de décision.
- Pour les jours in-window: `start_abs` / `end_abs` sont dérivés linéairement du combo choisi (`day_offset + combo.start_min/end_min`).
- Pour les jours hors fenêtre: `start_abs` / `end_abs` sont des constantes issues des données DB (`existing_shift_start_end_by_agent_day_ctx`) quand le jour est `WORKING` avec signature horaire connue, sinon `worked=0`.

Instrumentation de debug additive:

- `rpdouble_gap_minutes_required`
- `rpdouble_gap_violation_count_total`
- `rpdouble_gap_violation_sample` (max 10 entrées)

## Repos quotidien (HARD) — 12h20 / 14h si nuit impliquée

La contrainte de repos quotidien est **hard** et s'applique sur la temporalité réelle des services.

- Pour deux jours travaillés consécutifs `J -> J+1` d'un même agent:
  `start_abs(J+1) - end_abs(J) >= required_rest_minutes`.
- `required_rest_minutes = 840` si le combo de `J` ou de `J+1` implique de la nuit (`involves_night=True`), sinon `740`.
- Un "jour travaillé" pour cette règle = un jour avec une vraie affectation de service (combo avec `tranche_ids` non vide + `start/end` connus).
- `REST`, `LEAVE`, `ABSENT`, `ZCOT` sans tranche ne déclenchent pas la contrainte.
- La règle s'applique sur `context_days` complet, donc couvre:
  - in-window -> in-window,
  - contexte DB hors fenêtre -> in-window,
  - in-window -> contexte DB hors fenêtre.

Instrumentation debug additive (post-solve):

- `daily_rest_normal_minutes_required` (= 740)
- `daily_rest_night_minutes_required` (= 840)
- `daily_rest_violation_count_total`
- `daily_rest_violation_sample` (max 10 entrées)

## Daily Rest – Implementation Details

- Contrainte hard modélisée sur la timeline absolue du contexte (`context_days`):
  `start_abs_ctx[i+1] - end_abs_ctx[i] >= required_rest(i, i+1)` sous garde `OnlyEnforceIf([worked_ctx[i], worked_ctx[i+1]])`.
- Seuils:
  - `740` min (12h20) en standard,
  - `840` min (14h00) si nuit impliquée sur `i` ou `i+1`.
- Invariant structurel requis par le modèle:
  `worked_ctx == 1 => start_abs_ctx/end_abs_ctx valides`.
- `add_rest_compat_constraints` est conservée comme filtre de paires de combos in-window (réduction d'espace de recherche),
  tandis que la garantie métier finale du repos quotidien est portée par la contrainte absolue ci-dessus.

## GPT length rules

Définition GPT (pour cette règle) : séquence contiguë de jours `worked_day=True`, avec
`worked_day=True` **uniquement** pour `WORKING` ou `ZCOT`.

- `REST`, `LEAVE`, `ABSENT` cassent la séquence.
- Pour le contexte DB hors fenêtre :
  - `WORKING` n'est compté travaillé que si une signature exploitable + horaires de shift existent.
  - `ZCOT` est compté comme jour travaillé GPT.
  - un `WORKING` incohérent (sans assignment exploitable) n'ouvre pas artificiellement une GPT.

Contraintes hard GPT :

- longueur min = 3 jours consécutifs
- longueur max = 6 jours consécutifs

Conventions de frontière (DB ↔ fenêtre optimisée) :

- Le contexte DB est **observé** pour reconstruire les runs GPT (`WORKING` avec shift exploitable, `ZCOT`),
  mais la contrainte `min=3` n'est imposée que pour les starts **pilotables** dans la fenêtre et seulement
  si `J+1` et `J+2` sont aussi pilotables dans la fenêtre.
- La contrainte `max=6` s'applique sur les fenêtres glissantes de 7 jours qui touchent au moins un jour pilotable
  (fenêtre d'optimisation), pour éviter de sur-contraindre des segments purement historiques DB.
- En conséquence, les jours DB restent pris en compte comme contexte métier sans créer artificiellement des
  contradictions hard hors zone de décision.

Préférence soft GPT (à couverture égale) :

- `4` et `5` jours sont favorisés
- `3` et `6` jours sont moins désirables via `objective_terms.gpt_length_penalty`

Intégration hiérarchie objectif :

- les bornes `3..6` sont hard (non softenées)
- la pénalité GPT est un tie-breaker qualité, strictement sous la couverture
- la règle cohabite avec repos quotidien hard, RPDOUBLE et stabilité des affectations existantes

Stats associées (payload additif) :

- `solution_quality.gpt_count_total`
- `solution_quality.gpt_len_3_count_total`
- `solution_quality.gpt_len_4_count_total`
- `solution_quality.gpt_len_5_count_total`
- `solution_quality.gpt_len_6_count_total`
- `solution_quality.gpt_length_violation_count_total`
- `solution_quality.gpt_length_violation_sample`
- `solution_quality.gpt_len_3_penalized_total`
- `solution_quality.gpt_len_6_penalized_total`
- `solution_quality.gpt_length_penalty_total`
- `objective.objective_terms.gpt_length_penalty`

Diagnostics pré-solve GPT (model) :

- `model.gpt_ctx_worked_fixed_days_count_total`
- `model.gpt_ctx_worked_fixed_days_by_agent`
- `model.gpt_db_worked_days_count_total`
- `model.gpt_start_candidates_count_total`
- `model.gpt_min3_forced_extensions_count_total`
- `model.gpt_min3_forced_extensions_impossible_count_total`
- `model.gpt_max6_risk_windows_count_total`
- `model.gpt_hard_conflict_count_total`
- `model.gpt_hard_conflict_sample`
