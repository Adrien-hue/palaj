from __future__ import annotations

import logging
from typing import Any

from backend.app.services.solver.constants import RESULT_STATS_SCHEMA_VERSION
from backend.app.services.solver.stats import StatsCollector

logger = logging.getLogger(__name__)

_EXPECTED_GROUP_KEYS = (
    "meta",
    "timing",
    "model",
    "coverage",
    "objective",
    "solution_quality",
    "lns",
    "cp_sat",
)


def _strict_v3_payload(stats: dict[str, Any]) -> dict[str, Any]:
    normalized_stats: dict[str, Any] = {}
    for key in _EXPECTED_GROUP_KEYS:
        value = stats.get(key)
        normalized_stats[key] = value if isinstance(value, dict) else {}
    return {
        "result_stats_schema_version": RESULT_STATS_SCHEMA_VERSION,
        "stats": normalized_stats,
    }


def normalize_result_stats_for_api(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None

    if not isinstance(raw, dict):
        logger.warning(
            "result_stats.normalize.invalid_payload",
            extra={"payload_type": type(raw).__name__},
        )
        return None

    has_stats = isinstance(raw.get("stats"), dict)
    schema_version = raw.get("result_stats_schema_version")
    root_keys = set(raw.keys())

    if has_stats:
        if schema_version == RESULT_STATS_SCHEMA_VERSION and root_keys == {"result_stats_schema_version", "stats"}:
            return _strict_v3_payload(raw["stats"])

        return _strict_v3_payload(raw["stats"])

    collector = StatsCollector.from_env()
    try:
        grouped = collector.apply_verbosity(collector.build_grouped_stats(raw), collector.verbosity)
    except Exception:
        logger.warning(
            "result_stats.normalize.legacy_flat_only_fallback",
            extra={
                "detected_schema_version": schema_version,
                "has_stats": False,
                "root_key_count": len(root_keys),
                "root_keys_sample": sorted(list(root_keys))[:8],
            },
        )
        grouped = {key: {} for key in _EXPECTED_GROUP_KEYS}

    return _strict_v3_payload(grouped)
