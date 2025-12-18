import pytest
from core.utils import time_helpers as th

@pytest.mark.parametrize(
    "minutes,expected",
    [
        (90, "1h30"),
        (480, "8h"),
        (15, "15min"),
        (0, "0min"),
        (None, "—"),
        (125, "2h05"),
    ],
)
def test_minutes_to_duree_str(minutes, expected):
    assert th.minutes_to_duree_str(minutes) == expected
