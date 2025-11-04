from datetime import date, timedelta
from core.domain.services.periode_repos_service import PeriodeReposService


def test_detect_repos_simple(make_context_with_gpt):
    """Un seul jour de repos est correctement détecté."""
    service = PeriodeReposService()
    context = make_context_with_gpt(pattern=["POSTE", "REPOS", "POSTE"], include_left_repos = False, include_right_repos = False)

    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 1
    rp = periodes[0]
    assert rp.nb_jours == 1
    assert rp.start == date(2025, 1, 3)
    assert rp.end == date(2025, 1, 3)
    assert "simple" in rp.label().lower()


def test_detect_repos_double(make_context_with_gpt):
    """Deux jours de repos consécutifs → repos double."""
    service = PeriodeReposService()
    context = make_context_with_gpt(pattern=["POSTE", "REPOS", "REPOS", "POSTE"], include_left_repos = False, include_right_repos = False)

    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 1
    rp = periodes[0]
    assert rp.nb_jours == 2
    assert rp.start == date(2025, 1, 3)
    assert rp.end == date(2025, 1, 4)
    assert "double" in rp.label().lower()


def test_detect_repos_triple(make_context_with_gpt):
    """Trois jours de repos consécutifs → repos triple."""
    service = PeriodeReposService()
    context = make_context_with_gpt(pattern=["POSTE", "REPOS", "REPOS", "REPOS", "POSTE"], include_left_repos = False, include_right_repos = False)

    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 1
    rp = periodes[0]
    assert rp.nb_jours == 3
    assert "triple" in rp.label().lower()


def test_repos_separes_par_absence(make_context_with_gpt):
    """Deux repos séparés par des absences → deux périodes distinctes."""
    service = PeriodeReposService()
    context = make_context_with_gpt(pattern=["POSTE", "REPOS", "ABSENCE", "REPOS", "POSTE"], include_left_repos = False, include_right_repos = False)

    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 2
    jours = [p.nb_jours for p in periodes]
    assert jours == [1, 1]


def test_aucun_repos(make_context_with_gpt):
    """Aucun jour de repos → aucune période détectée."""
    service = PeriodeReposService()
    context = make_context_with_gpt(pattern=["POSTE", "ABSENCE", "ZCOT", "POSTE"], include_left_repos = False, include_right_repos = False)

    periodes = service.detect_periodes_repos(context)

    assert periodes == []


def test_detect_multiple_repos_complex(make_context_with_gpt):
    """Vérifie la détection correcte de plusieurs périodes de repos dans un planning complet."""
    pattern = [
        "POSTE", "POSTE", "POSTE",        # 1-3
        "REPOS", "REPOS",                 # 4-5 → double
        "ABSENCE", "ABSENCE",             # 6-7
        "POSTE", "POSTE",                 # 8-9
        "REPOS", "REPOS", "REPOS",        # 10-12 → triple
        "ZCOT",                           # 13
        "REPOS",                          # 14 → simple
        "POSTE",                          # 15
    ]

    service = PeriodeReposService()
    context = make_context_with_gpt(pattern=pattern, include_left_repos=False, include_right_repos=False)

    periodes = service.detect_periodes_repos(context)

    # On doit détecter 3 périodes distinctes : double, triple, simple
    assert len(periodes) == 3

    labels = [p.label().lower() for p in periodes]
    assert any("double" in l for l in labels)
    assert any("triple" in l for l in labels)
    assert any("simple" in l for l in labels)

    # Vérification des bornes temporelles
    assert periodes[0].start == date(2025, 1, 5)
    assert periodes[0].end == date(2025, 1, 6)
    assert periodes[1].start == date(2025, 1, 11)
    assert periodes[1].end == date(2025, 1, 13)
    assert periodes[2].start == date(2025, 1, 15)
    assert periodes[2].end == date(2025, 1, 15)

    # Vérifie que chaque durée en minutes est cohérente (repos simple ≈ 24h + 12h20, etc.)
    assert all(p.duree_minutes > 0 for p in periodes)