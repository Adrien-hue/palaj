from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Protocol

from .models import TrancheInfo

DUREE_MIN_MIN = 330
NIGHT_WINDOWS_DAY: tuple[tuple[int, int], ...] = ((21 * 60 + 30, 24 * 60), (0, 6 * 60 + 30))


class RhComboRulesEngine(Protocol):
    def is_day_valid(
        self,
        *,
        work_minutes: int,
        amplitude_minutes: int,
        involves_night: bool,
    ) -> bool: ...

    def min_rest_required(self, *, involves_night: bool) -> int: ...


@dataclass(frozen=True)
class DayCombo:
    id: int
    poste_id: int | None
    tranche_ids: tuple[int, ...]
    start_min: int | None
    end_min: int | None
    work_minutes: int
    amplitude_minutes: int
    involves_night: bool


@dataclass(frozen=True)
class TrancheWindow:
    tranche_id: int
    start_min: int
    end_min: int


class DefaultRhComboRulesEngine:
    AMPLITUDE_MAX_MIN = 660
    DUREE_MAX_STANDARD_MIN = 600
    DUREE_MAX_NUIT_MIN = 510
    REPOS_MIN_STANDARD_MIN = 740
    REPOS_MIN_NUIT_MIN = 840

    def is_day_valid(
        self,
        *,
        work_minutes: int,
        amplitude_minutes: int,
        involves_night: bool,
    ) -> bool:
        max_duration = self.DUREE_MAX_NUIT_MIN if involves_night else self.DUREE_MAX_STANDARD_MIN
        return amplitude_minutes <= self.AMPLITUDE_MAX_MIN and DUREE_MIN_MIN <= work_minutes <= max_duration

    def min_rest_required(self, *, involves_night: bool) -> int:
        return self.REPOS_MIN_NUIT_MIN if involves_night else self.REPOS_MIN_STANDARD_MIN


def interval_intersects(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def shift_involves_night(start_min: int, end_min: int) -> bool:
    """Return True if a [start,end) shift overlaps any night window on day axis.

    end_min may be > 1440 for shifts crossing midnight.
    """
    if end_min <= 24 * 60:
        return any(interval_intersects(start_min, end_min, n_start, n_end) for n_start, n_end in NIGHT_WINDOWS_DAY)

    segment1_start, segment1_end = start_min, 24 * 60
    segment2_start, segment2_end = 0, end_min - 24 * 60
    return interval_intersects(segment1_start, segment1_end, NIGHT_WINDOWS_DAY[0][0], NIGHT_WINDOWS_DAY[0][1]) or interval_intersects(
        segment2_start,
        segment2_end,
        NIGHT_WINDOWS_DAY[1][0],
        NIGHT_WINDOWS_DAY[1][1],
    )


def tranche_to_window(tranche: TrancheInfo) -> TrancheWindow:
    start_min = tranche.heure_debut.hour * 60 + tranche.heure_debut.minute
    end_min = tranche.heure_fin.hour * 60 + tranche.heure_fin.minute
    if end_min <= start_min:
        end_min += 24 * 60
    return TrancheWindow(tranche_id=tranche.id, start_min=start_min, end_min=end_min)


def _normalize_windows(windows: list[TrancheWindow]) -> list[TrancheWindow]:
    ordered = sorted(windows, key=lambda item: (item.start_min, item.end_min, item.tranche_id))
    normalized: list[TrancheWindow] = []
    cursor_end = -1
    for window in ordered:
        start = window.start_min
        end = window.end_min
        while start < cursor_end:
            start += 24 * 60
            end += 24 * 60
        cursor_end = max(cursor_end, end)
        normalized.append(TrancheWindow(tranche_id=window.tranche_id, start_min=start, end_min=end))
    return normalized


def build_day_combos_for_poste(
    *,
    tranches: list[TrancheInfo],
    rh_engine: RhComboRulesEngine,
    max_combination_size: int | None = None,
) -> list[DayCombo]:
    windows = [tranche_to_window(tranche) for tranche in sorted(tranches, key=lambda item: item.id)]
    if not windows:
        return []

    poste_id = tranches[0].poste_id
    combo_id = 0
    combos: list[DayCombo] = []

    max_size = max_combination_size or len(windows)
    max_size = min(max_size, len(windows))

    for size in range(1, max_size + 1):
        for subset in combinations(windows, size):
            normalized = _normalize_windows(list(subset))
            start_min = min(item.start_min for item in normalized)
            end_min = max(item.end_min for item in normalized)
            work_minutes = sum(item.end_min - item.start_min for item in normalized)
            amplitude_minutes = end_min - start_min
            involves_night = any(shift_involves_night(item.start_min, item.end_min) for item in normalized)
            if work_minutes < DUREE_MIN_MIN:
                continue
            if not rh_engine.is_day_valid(
                work_minutes=work_minutes,
                amplitude_minutes=amplitude_minutes,
                involves_night=involves_night,
            ):
                continue

            combos.append(
                DayCombo(
                    id=combo_id,
                    poste_id=poste_id,
                    tranche_ids=tuple(sorted(item.tranche_id for item in subset)),
                    start_min=start_min,
                    end_min=end_min,
                    work_minutes=work_minutes,
                    amplitude_minutes=amplitude_minutes,
                    involves_night=involves_night,
                )
            )
            combo_id += 1

    return combos


def build_rest_compatibility(
    *,
    combos: list[DayCombo],
    rh_engine: RhComboRulesEngine,
) -> set[tuple[int, int]]:
    compatible_pairs: set[tuple[int, int]] = set()
    for prev_combo in combos:
        for cur_combo in combos:
            if not prev_combo.tranche_ids or not cur_combo.tranche_ids:
                compatible_pairs.add((prev_combo.id, cur_combo.id))
                continue

            assert prev_combo.end_min is not None
            assert cur_combo.start_min is not None
            end_prev_global = prev_combo.end_min
            start_cur_global = cur_combo.start_min + 24 * 60
            rest_minutes = start_cur_global - end_prev_global
            min_rest = rh_engine.min_rest_required(
                involves_night=prev_combo.involves_night or cur_combo.involves_night
            )
            if rest_minutes >= min_rest:
                compatible_pairs.add((prev_combo.id, cur_combo.id))

    return compatible_pairs
