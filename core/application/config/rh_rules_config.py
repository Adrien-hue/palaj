# core/application/config/rh_rules_config.py
from core.rh_rules import (
    AmplitudeMaxRule,
    CongesAnnuelRule,
    DureeJourMoyenneSemestreRule,
    DureeTravailRule,
    GrandePeriodeTravailRule,
    QualificationIntegrityRule,
    RegimeReposAnnuelsRule,
    RegimeB25ReposMensuelRule,
    RegimeB25ReposSemestrielRule,
    ReposAnnuelRule,
    ReposDoubleRule,
    ReposQuotidienRule,
    RHRulesEngine,
)

def build_default_rh_engine() -> RHRulesEngine:
    return RHRulesEngine([
        AmplitudeMaxRule(),
        CongesAnnuelRule(),
        DureeJourMoyenneSemestreRule(),
        DureeTravailRule(),
        GrandePeriodeTravailRule(),
        QualificationIntegrityRule(),
        RegimeReposAnnuelsRule(),
        RegimeB25ReposMensuelRule(),
        RegimeB25ReposSemestrielRule(),
        ReposAnnuelRule(),
        ReposDoubleRule(),
        ReposQuotidienRule(),
    ])
