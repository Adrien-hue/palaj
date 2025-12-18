from datetime import time

import pytest

from core.domain.entities import Tranche


def test_tranche_parses_time_strings_and_round_trips():
    tranche = Tranche(id=1, nom="MJ", heure_debut="08:00", heure_fin="10:30", poste_id=99)

    assert tranche.heure_debut == time(8, 0)
    assert tranche.heure_fin == time(10, 30)

    serialized = tranche.to_dict()
    assert serialized == {
        "id": 1,
        "nom": "MJ",
        "heure_debut": "08:00",
        "heure_fin": "10:30",
        "poste_id": 99,
    }

    recreated = Tranche.from_dict(serialized)
    assert recreated.nom == "MJ"
    assert recreated.poste_id == 99
    assert recreated.heure_debut == time(8, 0)
    assert recreated.heure_fin == time(10, 30)


def test_tranche_invalid_time_string_raises_value_error():
    with pytest.raises(ValueError):
        Tranche(id=2, nom="Nuit", heure_debut="25:99", heure_fin="06:00", poste_id=1)


def test_tranche_duration_handles_midnight_crossing():
    tranche = Tranche(id=3, nom="Nuit", heure_debut="22:00", heure_fin="06:30", poste_id=1)

    assert tranche.duree_minutes() == 510
    assert tranche.duree() == 8.5
    assert tranche.duree_formatee() == "8h30min"


def test_tranche_set_poste_reference():
    tranche = Tranche(id=4, nom="Matin", heure_debut=time(7, 0), heure_fin=time(12, 0), poste_id=2)

    tranche.set_poste("POSTE") # pyright: ignore[reportArgumentType]
    assert tranche.poste == "POSTE"

def test_tranche_string_and_repr():
    tranche = Tranche(id=5, nom="Soirée", heure_debut=time(16, 0), heure_fin=time(23, 0), poste_id=3)

    text = str(tranche)
    assert "Tranche Soirée" in text
    assert "16:00" in text
    assert "23:00" in text
    assert "Tranche(Soirée" in repr(tranche)
    assert "16:00 - 23:00" in repr(tranche)
    assert "poste_id=3" in repr(tranche)