from typing import List, Protocol, Sequence
from core.rh_rules.models.rh_day import RhDay
from datetime import date


class GptAnalyzerProtocol(Protocol):
    def detect_from_rh_days(
        self,
        days: Sequence[RhDay],
        window_start: date,
        window_end: date,
    ) -> List:
        ...
