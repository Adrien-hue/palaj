from datetime import date, timedelta

from core.application.services.planning.repos_stats_analyzer import (
    ReposStatsAnalyzer,
)
from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import Agent, EtatJourAgent, TypeJour
from core.domain.models.work_day import WorkDay

def test_summarize_context_basic(make_workday):
    # RP : samedi-dimanche-lundi
    sam = date(2024, 1, 6)  # samedi
    dim = sam + timedelta(days=1)
    lun = sam + timedelta(days=2)

    wds = [make_workday(jour=d, type_label=TypeJour.REPOS) for d in [sam, dim, lun]]

    ctx = PlanningContext(
        agent=Agent(id=1, nom="T", prenom="A"),
        work_days=wds,
        date_reference=sam,
    )

    analyzer = ReposStatsAnalyzer()
    summary = analyzer.summarize_context(ctx)

    assert date(2024, 1, 6) in summary.rp_days
    assert date(2024, 1, 7) in summary.rp_days
    assert date(2024, 1, 8) in summary.rp_days
    assert summary.total_rp_days == 3
    assert summary.total_rp_sundays == 1
    assert summary.rp_triple == 1
    assert summary.rp_double == 0
    assert summary.rpsd == 1      # sam-dim
    assert summary.werp == 1      # sam-dim-lun → WERP
