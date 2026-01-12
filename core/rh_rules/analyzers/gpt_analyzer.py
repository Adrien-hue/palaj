# core/rh_rules/analyzers/gpt_analyzer.py
from __future__ import annotations

from datetime import date
from typing import List, Optional, Sequence

from core.domain.enums.day_type import DayType
from core.rh_rules.models.gpt_block import GptBlock
from core.rh_rules.models.rh_day import RhDay


class GptAnalyzer:
    """Detects and analyzes GPT blocks (consecutive WORKING/ZCOT days)."""

    def detect_from_rh_days(
        self,
        days: Sequence[RhDay],
        window_start: Optional[date] = None,
        window_end: Optional[date] = None,
    ) -> List[GptBlock]:
        days_sorted = sorted(days, key=lambda d: d.day_date)

        def is_gpt_work(d: RhDay) -> bool:
            return d.day_type in (DayType.WORKING, DayType.ZCOT)

        gpts: List[GptBlock] = []
        block: List[RhDay] = []

        def close_block() -> None:
            nonlocal block
            if not block:
                return

            start = block[0].day_date
            end = block[-1].day_date

            # "Truncated" means: the block touches the analysis window edge,
            # so we cannot know if it continues beyond the window.
            left_trunc = bool(window_start and start == window_start)
            right_trunc = bool(window_end and end == window_end)

            gpts.append(
                GptBlock(
                    days=tuple(block),
                    is_left_truncated=left_trunc,
                    is_right_truncated=right_trunc,
                )
            )
            block = []

        for d in days_sorted:
            if not is_gpt_work(d):
                close_block()
                continue

            if not block:
                block = [d]
                continue

            prev = block[-1]
            if (d.day_date - prev.day_date).days == 1:
                block.append(d)
            else:
                close_block()
                block = [d]

        close_block()
        return gpts
