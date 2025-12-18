# core/rh_rules/constants/regime_rules.py

# Durée de journée de service moyenne (en minutes)
REGIME_AVG_SERVICE_MINUTES = {
    0: 465,  # B → 7h45
    1: 465,  # B25 → 7h45
    2: 482,  # C → 8h02
}

# Tolérance acceptable sur la moyenne
REGIME_AVG_TOLERANCE_MINUTES = 5
