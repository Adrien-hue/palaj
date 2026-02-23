from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import pytest

pytestmark = [pytest.mark.unit, pytest.mark.planning]

from core.planning.solver.extractors import (
    expand_needs_to_slots,
    build_solver_agents,
)
from core.planning.solver.modifications import compute_modifications
from core.planning.solver.models import BaselineGroup, Need


# ============================================================
# SLOTS
# ============================================================

def test_expand_needs_to_slots_need_2_creates_2_slots():
    needs = [
        Need(
            poste_id=1,
            date=date(2026, 2, 20),
            tranche_id=10,
            required_count=2,
        )
    ]

    slots = expand_needs_to_slots(needs)

    assert len(slots) == 2
    assert slots[0].id == 0
    assert slots[1].id == 1

    assert slots[0].poste_id == 1
    assert slots[1].poste_id == 1

    assert slots[0].tranche_id == 10
    assert slots[1].tranche_id == 10

    assert slots[0].date == date(2026, 2, 20)
    assert slots[1].date == date(2026, 2, 20)


# ============================================================
# MODIFICATIONS (baseline diff)
# ============================================================

def test_compute_modifications_AB_to_AB_is_0():
    g = BaselineGroup(
        poste_id=1,
        date=date(2026, 2, 20),
        tranche_id=10,
        agents={1, 2},
    )

    sol = {(1, date(2026, 2, 20), 10): {1, 2}}

    assert compute_modifications([g], sol) == 0


def test_compute_modifications_AB_to_AC_is_1():
    g = BaselineGroup(
        poste_id=1,
        date=date(2026, 2, 20),
        tranche_id=10,
        agents={1, 2},
    )

    sol = {(1, date(2026, 2, 20), 10): {1, 3}}

    assert compute_modifications([g], sol) == 1


def test_compute_modifications_AB_to_CD_is_2():
    g = BaselineGroup(
        poste_id=1,
        date=date(2026, 2, 20),
        tranche_id=10,
        agents={1, 2},
    )

    sol = {(1, date(2026, 2, 20), 10): {3, 4}}

    assert compute_modifications([g], sol) == 2


def test_compute_modifications_empty_baseline_is_0():
    g = BaselineGroup(
        poste_id=1,
        date=date(2026, 2, 20),
        tranche_id=10,
        agents=set(),
    )

    sol = {(1, date(2026, 2, 20), 10): {1}}

    assert compute_modifications([g], sol) == 0


# ============================================================
# AGENT UNAVAILABILITY (ABSENT / LEAVE)
# ============================================================

@dataclass
class FakeAgent:
    id: int
    qualifications: list


@dataclass
class FakeAgentDay:
    agent_id: int
    day_date: date
    day_type: str
    is_off_shift: bool = False


def test_build_solver_agents_marks_absent_and_leave_as_unavailable():
    agents = [
        FakeAgent(id=1, qualifications=[]),
        FakeAgent(id=2, qualifications=[]),
    ]

    agent_days = [
        FakeAgentDay(
            agent_id=1,
            day_date=date(2026, 2, 20),
            day_type="absent",
        ),
        FakeAgentDay(
            agent_id=1,
            day_date=date(2026, 2, 21),
            day_type="leave",
        ),
        FakeAgentDay(
            agent_id=2,
            day_date=date(2026, 2, 20),
            day_type="off_shift",
        ),
    ]

    solver_agents = build_solver_agents(agents, agent_days=agent_days)
    by_id = {a.id: a for a in solver_agents}

    assert by_id[1].unavailable_dates == {
        date(2026, 2, 20),
        date(2026, 2, 21),
    }

    # off_shift ne doit PAS bloquer
    assert by_id[2].unavailable_dates == set()
