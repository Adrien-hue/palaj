import time
from functools import wraps
from collections import defaultdict
from typing import Callable, Any, Dict


class Profiler:
    """
    Outil global de profilage et de mesure des performances du projet.
    - Peut être utilisé comme décorateur via `@profiler.profile_call("nom")`
    - Conserve les statistiques cumulées
    - Fournit un rapport clair sur les fonctions mesurées
    """

    def __init__(self, enabled: bool = True, verbose: bool = False):
        self.enabled = enabled
        self.verbose = verbose
        self.stats: Dict[str, Dict[str, float | int]] = defaultdict(
            lambda: {"calls": 0, "total_time": 0.0, "min_time": float("inf"), "max_time": 0.0}
        )

    # --------------------------------------------------
    def profile_call(self, name: str | None = None):
        """Décorateur pour mesurer le temps d'exécution d'une fonction."""

        def decorator(func: Callable):
            label = name or func.__name__

            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not self.enabled:
                    return func(*args, **kwargs)

                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.perf_counter() - start
                    s = self.stats[label]
                    s["calls"] += 1
                    s["total_time"] += duration
                    s["min_time"] = min(s["min_time"], duration)
                    s["max_time"] = max(s["max_time"], duration)

                    if self.verbose:
                        print(f"[PROFILE] {label:<25} | {duration*1000:.2f} ms")

            return wrapper

        return decorator

    # --------------------------------------------------
    def summary(self) -> str:
        """Retourne une chaîne de résumé des stats cumulées."""
        if not self.stats:
            return "Aucune fonction mesurée."

        lines = [
            " /---------------------------------------------\\",
            "<============== PROFILER REPORT ===============>",
            " \\---------------------------------------------/",
        ]

        for name, s in self.stats.items():
            avg = s["total_time"] / s["calls"] if s["calls"] else 0
            lines.append(
                f"{name:<30} | calls={s['calls']:<5} "
                f"avg={avg*1000:>7.2f} ms "
                f"min={s['min_time']*1000:>7.2f} ms "
                f"max={s['max_time']*1000:>7.2f} ms "
                f"total={s['total_time']:.3f}s"
            )

        lines.append("-------------------------------------------------")
        return "\n".join(lines)

    def print_summary(self):
        """Affiche le rapport du profiler."""
        print(self.summary())

    # --------------------------------------------------
    def reset(self):
        """Réinitialise les statistiques."""
        self.stats.clear()


# Instance globale réutilisable dans tout le projet
profiler = Profiler(enabled=True, verbose=False)
