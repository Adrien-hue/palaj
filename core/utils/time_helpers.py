def minutes_to_duree_str(minutes: int) -> str:
    """
    Convertit un nombre de minutes en chaîne formatée : "Xh Ym" ou "Xh" / "Ym".
    
    Exemples :
    >>> minutes_to_duree_str(90)
    '1h30'
    >>> minutes_to_duree_str(480)
    '8h'
    >>> minutes_to_duree_str(15)
    '15min'
    >>> minutes_to_duree_str(0)
    '0min'
    """
    if minutes is None:
        return "—"
    
    heures, mins = divmod(int(minutes), 60)
    
    if heures > 0 and mins > 0:
        return f"{heures}h{mins:02d}"
    elif heures > 0:
        return f"{heures}h"
    else:
        return f"{mins}min"