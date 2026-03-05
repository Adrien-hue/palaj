from __future__ import annotations

from importlib import import_module
from typing import Iterable


def import_solver_modules(modules: Iterable[str]) -> list[str]:
    """Import solver modules by absolute path and return imported module names.

    Useful for architecture invariant tests (import-cycle smoke checks).
    """
    imported: list[str] = []
    for module_path in modules:
        module = import_module(module_path)
        imported.append(module.__name__)
    return imported


def is_monotonic_non_decreasing(values: Iterable[float]) -> bool:
    """Return ``True`` when values are monotonic non-decreasing."""
    last: float | None = None
    for value in values:
        current = float(value)
        if last is not None and current < last:
            return False
        last = current
    return True
