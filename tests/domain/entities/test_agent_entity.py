from core.domain.entities import Agent


def test_agent_to_dict_from_dict_round_trip():
    source = {
        "id": 1,
        "nom": "Dupont",
        "prenom": "Alice",
        "code_personnel": "A123",
        "regime_id": 7,
    }

    agent = Agent.from_dict(source)

    assert agent.id == 1
    assert agent.nom == "Dupont"
    assert agent.prenom == "Alice"
    assert agent.code_personnel == "A123"
    assert agent.regime_id == 7
    assert agent.to_dict() == source


def test_agent_string_and_repr_display_counts():
    agent = Agent(2, "Durand", "Bob", code_personnel="Z007")

    text = str(agent)

    assert "Durand" in text and "Bob" in text
    assert "Qualifications:" in text
    assert "Affectations:" in text
    assert "États journaliers:" in text
    assert "<Agent id=2" in repr(agent)


def test_agent_property_setters_store_related_entities():
    agent = Agent(3, "Martin", "Clara")

    agent.set_regime("REGIME") # pyright: ignore[reportArgumentType]
    agent.set_qualifications(["Q1", "Q2"]) # pyright: ignore[reportArgumentType]
    agent.set_affectations(["A1"]) # pyright: ignore[reportArgumentType]
    agent.set_etat_jours(["E1", "E2"]) # pyright: ignore[reportArgumentType]

    assert agent.regime == "REGIME"
    assert agent.qualifications == ["Q1", "Q2"]
    assert agent.affectations == ["A1"]
    assert agent.etat_jours == ["E1", "E2"]


def test_agent_full_name():
    agent = Agent(4, "Leroy", "Dana")
    assert agent.get_full_name() == "Dana Leroy"