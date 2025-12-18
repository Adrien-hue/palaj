from core.domain.entities import Poste


def test_poste_to_dict_and_from_dict_round_trip():
    source = {"id": 11, "nom": "GM J"}

    poste = Poste.from_dict(source)
    assert poste.id == 11
    assert poste.nom == "GM J"
    assert poste.to_dict() == source


def test_poste_string_and_repr_display_counts():
    poste = Poste(5, "RLIV6P")

    text = str(poste)
    assert "RLIV6P" in text
    assert "Non chargé" in text  # when qualifications not injected yet
    assert "<Poste RLIV6P>" == repr(poste)


def test_poste_setters_store_relations():
    poste = Poste(6, "SEC")

    poste.set_qualifications(["Q1", "Q2"])
    poste.set_tranches(["T1"])

    assert poste.qualifications == ["Q1", "Q2"]
    assert poste.tranches == ["T1"]