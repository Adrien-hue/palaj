from core.rh_rules.rule_repos_qualifie_info import ReposQualifieInfoRule
from core.utils.domain_alert import Severity

def test_repos_simple(make_context_with_gpt):
    """Un seul jour de repos → Repos simple détecté"""
    context = make_context_with_gpt(pattern=["POSTE", "REPOS", "POSTE"], include_left_repos = False, include_right_repos = False)
    rule = ReposQualifieInfoRule()
    ok, alerts = rule.check(context)

    assert ok
    assert len(alerts) == 1
    msg = alerts[0].message.lower()
    assert "rp simple" in msg
    assert alerts[0].severity == Severity.INFO


def test_repos_double(make_context_with_gpt):
    """Deux jours consécutifs de repos → Repos double détecté"""
    context = make_context_with_gpt(pattern=["POSTE", "REPOS", "REPOS", "POSTE"], include_left_repos = False, include_right_repos = False)
    rule = ReposQualifieInfoRule()
    ok, alerts = rule.check(context)

    assert ok
    assert any("rp double" in a.message.lower() for a in alerts)
    assert all(a.severity == Severity.INFO for a in alerts)


def test_repos_triple(make_context_with_gpt):
    """Trois jours consécutifs de repos → Repos triple détecté"""
    context = make_context_with_gpt(pattern=["POSTE", "REPOS", "REPOS", "REPOS", "POSTE"], include_left_repos = False, include_right_repos = False)
    rule = ReposQualifieInfoRule()
    ok, alerts = rule.check(context)

    assert ok
    assert any("rp triple" in a.message.lower() for a in alerts)


def test_repos_separes_par_absence(make_context_with_gpt):
    """Repos séparés par des absences → Deux repos simples distincts"""
    context = make_context_with_gpt(pattern=["POSTE", "REPOS", "ABSENCE", "REPOS", "POSTE"], include_left_repos = False, include_right_repos = False)
    rule = ReposQualifieInfoRule()
    ok, alerts = rule.check(context)

    assert ok
    # On doit avoir deux repos simples
    simples = [a for a in alerts if "rp simple" in a.message.lower()]
    assert len(simples) == 2


def test_aucun_repos(make_context_with_gpt):
    """Aucun jour de repos → Aucune alerte"""
    context = make_context_with_gpt(pattern=["POSTE", "ABSENCE", "ZCOT", "POSTE"], include_left_repos = False, include_right_repos = False)
    rule = ReposQualifieInfoRule()
    ok, alerts = rule.check(context)

    assert ok
    assert alerts == []
