from datetime import timedelta
from core.rh_rules.rule_repos_double import ReposDoubleRule
from core.domain.entities import TypeJour

# ---------------------------------------------------------------------
# 🧪 TESTS DE LA RÈGLE REPOS DOUBLE
# ---------------------------------------------------------------------

def test_repos_double_ok(make_context_with_gpt):
    """✅ Cas conforme : GPT de 6 jours suivie de 2 jours de repos."""
    context = make_context_with_gpt(pattern=["POSTE", "POSTE", "POSTE", "POSTE", "POSTE", "POSTE", "REPOS"])

    # Transformer les 2 jours après la GPT en REPOS
    last_gpt_day = context.work_days[-2].jour
    for wd in context.work_days:
        if wd.jour > last_gpt_day:
            wd.etat.type_jour = TypeJour.REPOS

    rule = ReposDoubleRule()
    ok, alerts = rule.check(context)

    assert ok is True
    assert not any(a.severity.name in ("ERROR", "WARNING") for a in alerts)

def test_repos_triple_ok(make_context_with_gpt):
    """✅ GPT de 6 jours suivie de 3 jours de repos : conforme."""
    context = make_context_with_gpt(pattern=["POSTE", "POSTE", "POSTE", "POSTE", "POSTE", "POSTE", "REPOS", "REPOS"])

    rule = ReposDoubleRule()
    ok, alerts = rule.check(context)

    assert ok is True
    assert alerts == []


def test_repos_double_insuffisant(make_context_with_gpt):
    """⚠️ GPT 6 jours suivie d’1 seul jour de repos → alerte attendue."""
    context = make_context_with_gpt(pattern=["POSTE", "POSTE", "POSTE", "POSTE", "POSTE", "POSTE", "REPOS", "POSTE"])

    # Seulement 1 jour de repos après la GPT
    last_gpt_day = context.work_days[-2].jour
    one_rest_day = context.work_days[-1]
    one_rest_day.etat.type_jour = TypeJour.REPOS

    rule = ReposDoubleRule()
    ok, alerts = rule.check(context)

    assert ok is False
    assert any("repos double" in a.message.lower() for a in alerts)
    assert any(a.severity.name == "ERROR" for a in alerts)


def test_pas_de_gpt_6_jours(make_context_with_gpt):
    """✅ GPT < 6 jours → la règle ne s’applique pas."""
    context = make_context_with_gpt(nb_jours=4)
    rule = ReposDoubleRule()
    ok, alerts = rule.check(context)

    assert ok is True
    assert alerts == []

# ---------------------------------------------------------------------
# 🚧 CAS BORDS DU PLANNING
# ---------------------------------------------------------------------

def test_gpt_fin_planning(make_context_with_gpt):
    """🕐 GPT de 6 jours à la fin du planning → non évaluable → pas d'alerte."""
    context = make_context_with_gpt(pattern=["POSTE", "POSTE", "POSTE", "POSTE", "POSTE", "POSTE", "REPOS"], include_right_repos=False)
    for d in context.work_days:
        print(d)

    rule = ReposDoubleRule()
    ok, alerts = rule.check(context)
    print("[DEBUG] OK:", ok)
    print("[DEBUG] alerts:", alerts)

    assert ok is True
    assert all("repos double" not in a.message.lower() for a in alerts)


def test_aucune_gpt(make_context_with_gpt):
    """✅ Aucun jour travaillé (repos uniquement) → rien à signaler."""
    context = make_context_with_gpt(pattern=["REPOS"] * 5)
    rule = ReposDoubleRule()
    ok, alerts = rule.check(context)

    assert ok is True
    assert alerts == []