from datetime import date

from core.domain.entities import Qualification


def test_qualification_to_dict_and_from_dict_round_trip():
    qualification = Qualification(agent_id=1, poste_id=2, date_qualification=date(2024, 2, 1))

    serialized = qualification.to_dict()
    assert serialized == {
        "agent_id": 1,
        "poste_id": 2,
        "date_qualification": "2024-02-01",
    }

    recreated = Qualification.from_dict(serialized)
    assert recreated.agent_id == 1
    assert recreated.poste_id == 2
    assert recreated.date_qualification == date(2024, 2, 1)


def test_qualification_string_and_repr_include_ids():
    qualification = Qualification(agent_id=3, poste_id=4)
    assert "agent=3" in repr(qualification)
    assert "poste=4" in str(qualification)


def test_qualification_setters_store_relations():
    qualification = Qualification(agent_id=5, poste_id=6)

    qualification.set_agent("AGENT") # pyright: ignore[reportArgumentType]
    qualification.set_poste("POSTE") # pyright: ignore[reportArgumentType]

    assert qualification.agent == "AGENT"
    assert qualification.poste == "POSTE"