# Solver OR-Tools (backend/app/services/solver)

## CI note (PR4 scope)

Cette zone contient la refacto non-breaking du solver (`constants.py`, `diagnostics.py`, docstrings d'architecture, invariants de tests).

- Le run global `pytest -q` peut échouer **en collecte** sur ce repository à cause de modules manquants hors scope solver (état déjà présent sur `main`).
- Cette PR **ne modifie pas** ces zones hors solver.
- La validation pertinente pour cette PR est :

```bash
pytest -q tests/backend/services/solver/test_ortools_solver.py
```

- Pour un smoke ciblé architecture/stats :

```bash
pytest -q tests/backend/services/solver/test_ortools_solver.py -k "architecture_modules_import_without_cycles or grouped_stats_meta_solver_version_v3"
```

## Invariants de contrat

- Clés `result_stats` flat conservées (non-breaking).
- Grouped stats conservées, avec ajout additif : `stats.meta.solver_version = "v3"`.
- `RESULT_STATS_SCHEMA_VERSION` est la source unique pour `meta.schema_version` et `result_stats_schema_version`.
