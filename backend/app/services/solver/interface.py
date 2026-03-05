from __future__ import annotations

from typing import Protocol

from backend.app.services.solver.models import SolverInput, SolverOutput


class SolverService(Protocol):
    def generate(self, solver_input: SolverInput) -> SolverOutput:
        ...
