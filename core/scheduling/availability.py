from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Dict, Iterable, Set

from core.domain.entities.etat_jour_agent import EtatJourAgent, TypeJour


INDISPO_TYPES_DEFAULT: Set[TypeJour] = {
    TypeJour.ABSENCE,
    TypeJour.CONGE,
    TypeJour.REPOS,
}


def build_indispo_agent_ids_by_day(
    etats: Iterable[EtatJourAgent],
    indispo_types: Set[TypeJour] = INDISPO_TYPES_DEFAULT,
) -> Dict[date, Set[int]]:
    """
    Retourne {jour -> {agent_id,...}} pour tous les états dont type_jour est indispo.
    (ZCOT n'est pas indispo : agent réaffectable.)
    """
    result: Dict[date, Set[int]] = defaultdict(set)
    for e in etats:
        if e.type_jour in indispo_types:
            result[e.jour].add(e.agent_id)
    return dict(result)
