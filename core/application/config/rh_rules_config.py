from core.rh_rules import (
    AmplitudeMaxRule,
    DureeTravailRule,
    GrandePeriodeTravailRule,
    ReposDoubleRule,
    ReposQualifieInfoRule,
    ReposQuotidienRule,
    RHRulesEngine,
)

def build_default_rh_engine() -> RHRulesEngine:
    return RHRulesEngine([
        AmplitudeMaxRule(),
        DureeTravailRule(),
        GrandePeriodeTravailRule(),
        ReposDoubleRule(),
        ReposQualifieInfoRule(),
        ReposQuotidienRule(),
    ])
