from __future__ import annotations

from backend.app.services.solver.constants import RESULT_STATS_SCHEMA_VERSION
from backend.app.services.solver.stats_normalizer import normalize_result_stats_for_api


def _grouped_stats() -> dict:
    return {
        "meta": {},
        "timing": {},
        "model": {},
        "coverage": {"coverage_ratio": 1},
        "objective": {},
        "solution_quality": {},
        "lns": {},
        "cp_sat": {},
    }


def test_normalize_result_stats_for_api_mixed_payload_keeps_strict_v3_shape():
    raw = {
        "result_stats_schema_version": 2,
        "stats": _grouped_stats(),
        "absence_count": 0,
        "demand_count": 12,
    }

    normalized = normalize_result_stats_for_api(raw)

    assert normalized is not None
    assert set(normalized.keys()) == {"result_stats_schema_version", "stats"}
    assert normalized["result_stats_schema_version"] == RESULT_STATS_SCHEMA_VERSION


def test_normalize_result_stats_for_api_strict_v3_is_stable():
    raw = {
        "result_stats_schema_version": RESULT_STATS_SCHEMA_VERSION,
        "stats": _grouped_stats(),
    }

    normalized = normalize_result_stats_for_api(raw)

    assert normalized == raw


def test_normalize_result_stats_for_api_none_returns_none():
    assert normalize_result_stats_for_api(None) is None
