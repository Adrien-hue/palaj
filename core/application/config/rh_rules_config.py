# core/application/config/rh_rules_config.py
from enum import Enum

from core.rh_rules import (
    AmplitudeMaxRule,
    CongesAnnuelRule,
    DureeJourMoyenneSemestreRule,
    DureeTravailRule,
    GrandePeriodeTravailRule,
    QualificationIntegrityRule,
    RegimeReposAnnuelsRule,
    RegimeReposMensuelsRule,
    RegimeReposSemestrielsRule,
    ReposAnnuelRule,
    ReposDoubleRule,
    ReposQuotidienRule,
    RHRulesEngine,
)

class RhEngineProfile(str, Enum):
    FAST = "fast"
    FULL = "full"
    ANNUAL = "annual"

ALL_RULES = [
    AmplitudeMaxRule,
    CongesAnnuelRule,
    DureeJourMoyenneSemestreRule,
    DureeTravailRule,
    GrandePeriodeTravailRule,
    QualificationIntegrityRule,
    RegimeReposAnnuelsRule,
    RegimeReposMensuelsRule,
    RegimeReposSemestrielsRule,
    ReposAnnuelRule,
    ReposDoubleRule,
    ReposQuotidienRule,
]

PROFILE_RULES = {
    "fast": [
        AmplitudeMaxRule,
        DureeTravailRule,
        GrandePeriodeTravailRule,
        QualificationIntegrityRule,
        RegimeReposMensuelsRule,
        ReposDoubleRule,
        ReposQuotidienRule,
    ],
    "full": ALL_RULES,
    "annual": [
        CongesAnnuelRule,
        RegimeReposAnnuelsRule,
        ReposAnnuelRule,
    ],
}

def build_rh_engine(profile: str = "full") -> RHRulesEngine:
    rule_classes = PROFILE_RULES.get(profile, PROFILE_RULES["full"])
    return RHRulesEngine([cls() for cls in rule_classes])