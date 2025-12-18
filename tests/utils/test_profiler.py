import pytest

from core.utils.profiler import Profiler, profiler  # adapte le chemin si besoin


def test_summary_without_stats_returns_message():
    p = Profiler(enabled=True, verbose=False)

    summary = p.summary()

    assert "Aucune fonction mesurée." in summary


def test_profile_call_with_label_and_enabled(monkeypatch):
    p = Profiler(enabled=True, verbose=False)

    # On contrôle perf_counter pour rendre le test déterministe
    times = iter([1.0, 1.1])  # durée 0.1s

    def fake_perf_counter():
        return next(times)

    monkeypatch.setattr("core.utils.profiler.time.perf_counter", fake_perf_counter)

    @p.profile_call("custom_label")
    def my_func(x, y):
        return x + y

    result = my_func(2, 3)

    assert result == 5
    assert "custom_label" in p.stats
    s = p.stats["custom_label"]
    assert s["calls"] == 1
    assert pytest.approx(s["total_time"], rel=1e-6) == 0.1
    assert pytest.approx(s["min_time"], rel=1e-6) == 0.1
    assert pytest.approx(s["max_time"], rel=1e-6) == 0.1


def test_profile_call_uses_function_name_when_no_label(monkeypatch):
    p = Profiler(enabled=True, verbose=False)

    times = iter([2.0, 2.2])  # 0.2s

    def fake_perf_counter():
        return next(times)

    monkeypatch.setattr("core.utils.profiler.time.perf_counter", fake_perf_counter)

    @p.profile_call()
    def some_function():
        return "ok"

    result = some_function()
    assert result == "ok"

    # Le label doit être le nom de la fonction
    assert "some_function" in p.stats
    s = p.stats["some_function"]
    assert s["calls"] == 1
    assert pytest.approx(s["total_time"], rel=1e-6) == 0.2


def test_profile_call_disabled_does_not_record_stats(monkeypatch):
    p = Profiler(enabled=False, verbose=True)  # verbose ne doit pas être utilisé

    called = {"count": 0}

    @p.profile_call("disabled_func")
    def dummy():
        called["count"] += 1
        return 42

    result = dummy()

    assert result == 42
    assert called["count"] == 1

    # Le profiler ne doit rien avoir enregistré
    assert "disabled_func" not in p.stats
    # Aucun accès n'a créé d'entrée dans le defaultdict
    assert len(p.stats) == 0


def test_profile_call_updates_min_and_max_over_multiple_calls(monkeypatch):
    p = Profiler(enabled=True, verbose=False)

    # 2 appels : durées 0.1s puis 0.3s
    times = iter([1.0, 1.1, 2.0, 2.3])

    def fake_perf_counter():
        return next(times)

    monkeypatch.setattr("core.utils.profiler.time.perf_counter", fake_perf_counter)

    @p.profile_call("multi")
    def func():
        return "x"

    func()
    func()

    s = p.stats["multi"]
    assert s["calls"] == 2
    assert pytest.approx(s["total_time"], rel=1e-6) == 0.4
    assert pytest.approx(s["min_time"], rel=1e-6) == 0.1
    assert pytest.approx(s["max_time"], rel=1e-6) == 0.3


def test_profile_call_with_exception_still_records_stats(monkeypatch):
    p = Profiler(enabled=True, verbose=False)

    times = iter([10.0, 10.05])  # 0.05s

    def fake_perf_counter():
        return next(times)

    monkeypatch.setattr("core.utils.profiler.time.perf_counter", fake_perf_counter)

    @p.profile_call("failing_func")
    def failing():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        failing()

    # Malgré l'exception, les stats doivent être mises à jour
    assert "failing_func" in p.stats
    s = p.stats["failing_func"]
    assert s["calls"] == 1
    assert pytest.approx(s["total_time"], rel=1e-6) == 0.05


def test_verbose_mode_prints_each_call(monkeypatch, capsys):
    p = Profiler(enabled=True, verbose=True)

    times = iter([3.0, 3.01])  # 0.01s

    def fake_perf_counter():
        return next(times)

    monkeypatch.setattr("core.utils.profiler.time.perf_counter", fake_perf_counter)

    @p.profile_call("verbose_func")
    def func():
        return "ok"

    func()
    captured = capsys.readouterr()
    # La ligne de profilage doit être imprimée
    assert "[PROFILE]" in captured.out
    assert "verbose_func" in captured.out


def test_summary_format_with_stats(monkeypatch):
    p = Profiler(enabled=True, verbose=False)

    times = iter([1.0, 1.1, 2.0, 2.3])  # 0.1 et 0.3 → avg 0.2s

    def fake_perf_counter():
        return next(times)

    monkeypatch.setattr("core.utils.profiler.time.perf_counter", fake_perf_counter)

    @p.profile_call("func_for_summary")
    def func():
        return None

    func()
    func()

    summary = p.summary().splitlines()

    # En-tête présent
    assert any("PROFILER REPORT" in line for line in summary)

    # Ligne de stats pour la fonction
    stats_lines = [l for l in summary if "func_for_summary" in l]
    assert len(stats_lines) == 1
    line = stats_lines[0]

    # Vérifications de base sur le contenu formaté
    assert "calls=2" in line
    # avg ~ 200 ms, min ~ 100 ms, max ~ 300 ms, total ~ 0.400s
    assert "avg=" in line and "200.00 ms" in line
    assert "min=" in line and "100.00 ms" in line
    assert "max=" in line and "300.00 ms" in line
    assert "total=0.400" in line


def test_print_summary_uses_summary(capsys):
    p = Profiler(enabled=True, verbose=False)

    @p.profile_call("for_print")
    def func():
        return None

    func()

    p.print_summary()
    out = capsys.readouterr().out

    # Le contenu de summary() doit être affiché
    assert "PROFILER REPORT" in out
    assert "for_print" in out


def test_reset_clears_stats(monkeypatch):
    p = Profiler(enabled=True, verbose=False)

    times = iter([5.0, 5.02])  # 0.02s

    def fake_perf_counter():
        return next(times)

    monkeypatch.setattr("core.utils.profiler.time.perf_counter", fake_perf_counter)

    @p.profile_call("to_reset")
    def func():
        return None

    func()
    assert "to_reset" in p.stats

    p.reset()
    assert len(p.stats) == 0
    # summary doit maintenant renvoyer le message "aucune fonction..."
    assert "Aucune fonction mesurée." in p.summary()


def test_global_profiler_instance_exists_and_configured():
    # On vérifie que l'instance globale est bien créée et configurable
    assert isinstance(profiler, Profiler)
    assert profiler.enabled is True
    assert profiler.verbose is True
