from datetime import datetime, date, time, timedelta

def combine_datetime(jour: date, heure: time) -> datetime:
    """Combine une date et une heure en datetime."""
    return datetime.combine(jour, heure)

def end_datetime_with_rollover(jour: date, debut: time, fin: time) -> datetime:
    """
    Retourne le datetime de fin réel, tenant compte du passage de minuit.
    Exemple : 22:00 → 06:00 devient jour+1 à 06:00
    """
    dt_debut = combine_datetime(jour, debut)
    dt_fin = combine_datetime(jour, fin)
    if fin <= debut:
        dt_fin += timedelta(days=1)
    return dt_fin

def duration_hours_between(h1: time, h2: time) -> float:
    """Calcule la durée (en heures), avec passage minuit si besoin."""
    dt1 = combine_datetime(date.today(), h1)
    dt2 = combine_datetime(date.today(), h2)
    if dt2 <= dt1:
        dt2 += timedelta(days=1)
    return (dt2 - dt1).total_seconds() / 3600

def overlap_hours(period1: tuple[time, time], period2: tuple[time, time]) -> float:
    """Calcule le chevauchement entre deux périodes horaires (en heures)."""
    t1_start, t1_end = period1
    t2_start, t2_end = period2

    dt1_start = combine_datetime(date.today(), t1_start)
    dt1_end = combine_datetime(date.today(), t1_end)
    if t1_end <= t1_start:
        dt1_end += timedelta(days=1)

    dt2_start = combine_datetime(date.today(), t2_start)
    dt2_end = combine_datetime(date.today(), t2_end)
    if t2_end <= t2_start:
        dt2_end += timedelta(days=1)

    overlap = max(timedelta(0), min(dt1_end, dt2_end) - max(dt1_start, dt2_start))
    return overlap.total_seconds() / 3600

def is_tranche_nocturne(debut: time, fin: time) -> bool:
    """Retourne True si la tranche intersecte la période nocturne (21h30 - 6h30)."""
    return debut >= time(21, 30) or fin <= time(6, 30)

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