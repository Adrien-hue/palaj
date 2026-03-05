from __future__ import annotations

# Public grouped stats metadata.
RESULT_STATS_SCHEMA_VERSION = 3
SOLVER_VERSION = "v3"

# Stats payload caps by verbosity.
STATS_PAYLOAD_CAPS = {
    "debug": {
        "combo_rejected_samples": 50,
        "combo_allowed_samples": 50,
        "missing_tranche_in_any_combo_sample": 50,
        "top_understaff_days": 20,
        "lns_iteration_history": 100,
        "cp_sat_best_objective_points": 200,
        "understaff_by_day_weighted": 366,
    },
    "compact": {
        "combo_rejected_samples": 10,
        "combo_allowed_samples": 10,
        "missing_tranche_in_any_combo_sample": 10,
        "top_understaff_days": 10,
        "lns_iteration_history": 20,
        "cp_sat_best_objective_points": 50,
        "understaff_by_day_weighted": 31,
    },
}

# CP-SAT deterministic defaults.
CP_SAT_DEFAULT_NUM_SEARCH_WORKERS = 1
CP_SAT_DEFAULT_RANDOM_SEED = 0

# LNS guardrails and history sizing.
MIN_LNS_REMAINING_SECONDS_TO_RUN_ITER = 0.2
LNS_ITER_OVERHEAD_SECONDS = 0.05
MIN_LNS_CP_SAT_TIME_LIMIT_SECONDS = 0.2
MAX_LNS_HISTORY_ITEMS = 200
LNS_RECENT_STATUS_WINDOW = 10
