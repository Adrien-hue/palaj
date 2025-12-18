from datetime import date, datetime, time

import pytest

from core.adapters.entity_mapper import EntityMapper


# ---------------------------------------------------------------------
# Fakes / helpers pour simuler les modèles SQLAlchemy
# ---------------------------------------------------------------------


class FakeMapperAttrs:
    """Simule l'objet `.__mapper__.attrs` de SQLAlchemy avec une méthode .keys()."""

    def __init__(self, keys):
        self._keys = list(keys)

    def keys(self):
        return self._keys


class FakeMapper:
    """Simule un mapper SQLAlchemy minimal."""

    def __init__(self, keys):
        self.attrs = FakeMapperAttrs(keys)


class SimpleEntity:
    """Entité métier simple pour les tests."""

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


class EntityWithRelationId:
    """Entité qui attend un champ relation_id issu d'une relation."""

    def __init__(self, id: int, regime_id: int):
        self.id = id
        self.regime_id = regime_id
        # cache privé pour relation
        self._regime = None


# ---------------------------------------------------------------------
# model_to_entity : cas de base / custom to_entity
# ---------------------------------------------------------------------


def test_model_to_entity_returns_none_when_model_is_none():
    result = EntityMapper.model_to_entity(None, SimpleEntity)
    assert result is None


def test_model_to_entity_uses_custom_to_entity_when_available():
    class ModelWithCustom:
        def to_entity(self):
            return SimpleEntity(id=1, name="Custom")

    model = ModelWithCustom()
    entity = EntityMapper.model_to_entity(model, SimpleEntity)

    assert isinstance(entity, SimpleEntity)
    assert entity.id == 1
    assert entity.name == "Custom"


def test_model_to_entity_custom_to_entity_wrong_type_raises_type_error():
    class OtherEntity:
        pass

    class ModelWithBadToEntity:
        def to_entity(self):
            return OtherEntity()

    model = ModelWithBadToEntity()

    with pytest.raises(TypeError):
        EntityMapper.model_to_entity(model, SimpleEntity)


# ---------------------------------------------------------------------
# model_to_entity : mapping via __mapper__
# ---------------------------------------------------------------------


def test_model_to_entity_with_mapper_and_primitives():
    class FakeModel:
        __mapper__ = FakeMapper(keys=["id", "name", "ignored"])

        def __init__(self):
            self.id = 10
            self.name = "Alice"
            self.ignored = object()  # non primitif → ne doit pas être mappé

    model = FakeModel()
    entity = EntityMapper.model_to_entity(model, SimpleEntity)

    assert isinstance(entity, SimpleEntity)
    assert entity.id == 10
    assert entity.name == "Alice"


def test_model_to_entity_without_mapper_falls_back_to_vars():
    class NoMapperModel:
        def __init__(self):
            self.id = 42
            self.name = "Bob"
            self._private = "secret"  # doit être ignoré

    model = NoMapperModel()
    entity = EntityMapper.model_to_entity(model, SimpleEntity)

    assert isinstance(entity, SimpleEntity)
    assert entity.id == 42
    assert entity.name == "Bob"
    # _private ne doit pas se retrouver dans les kwargs du ctor → pas d'erreur


def test_model_to_entity_maps_relation_to_id_field_when_present():
    class Relation:
        def __init__(self, id):
            self.id = id

    class ModelWithRelation:
        __mapper__ = FakeMapper(keys=["id", "regime"])

        def __init__(self):
            self.id = 5
            self.regime = Relation(id=99)

    model = ModelWithRelation()
    entity = EntityMapper.model_to_entity(model, EntityWithRelationId)

    assert isinstance(entity, EntityWithRelationId)
    assert entity.id == 5
    assert entity.regime_id == 99


def test_model_to_entity_handles_private_relation_cache_gracefully():
    """
    Vérifie que la logique qui tente de remplir les caches privés (_relation)
    ne lève pas d'erreur même si l'entité cible n'existe pas dans core.domain.entities.
    """

    class DummyRelation:
        def __init__(self, id):
            self.id = id

    class ModelWithRelation:
        __mapper__ = FakeMapper(keys=["id", "foo"])

        def __init__(self):
            self.id = 1
            self.foo = DummyRelation(id=123)

    class EntityWithPrivateCache:
        def __init__(self, id: int):
            self.id = id
            self._foo = None  # cache privé que le mapper va essayer de remplir

    model = ModelWithRelation()
    entity = EntityMapper.model_to_entity(model, EntityWithPrivateCache)

    assert isinstance(entity, EntityWithPrivateCache)
    assert entity.id == 1
    # On ne sait pas si _foo sera effectivement rempli (selon le contenu de core.domain.entities),
    # mais au moins, aucune exception n'a été levée.


# ---------------------------------------------------------------------
# entity_to_model
# ---------------------------------------------------------------------


def test_entity_to_model_returns_none_when_entity_is_none():
    class FakeModelClass:
        __mapper__ = FakeMapper(keys=["id"])

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    result = EntityMapper.entity_to_model(None, FakeModelClass) # pyright: ignore[reportArgumentType]
    assert result is None


def test_entity_to_model_filters_fields_using_mapper_attrs():
    class FakeModelClass:
        __mapper__ = FakeMapper(keys=["id", "name"])

        def __init__(self, **kwargs):
            self.id = kwargs.get("id")
            self.name = kwargs.get("name")
            self.extra = kwargs.get("extra", None)

    class Entity:
        def __init__(self):
            self.id = 7
            self.name = "Charlie"
            self.extra = "should_not_be_mapped"

    entity = Entity()
    model = EntityMapper.entity_to_model(entity, FakeModelClass) # pyright: ignore[reportArgumentType]

    assert isinstance(model, FakeModelClass)
    assert model.id == 7
    assert model.name == "Charlie"
    # "extra" ne fait pas partie des attrs du mapper → ne doit pas être passé
    assert model.extra is None


# ---------------------------------------------------------------------
# update_model_from_entity
# ---------------------------------------------------------------------


def test_update_model_from_entity_returns_same_model_when_model_or_entity_is_none():
    class FakeModel:
        __mapper__ = FakeMapper(keys=["id", "name"])

        def __init__(self, id, name):
            self.id = id
            self.name = name

    model = FakeModel(id=1, name="Initial")

    # None model
    res1 = EntityMapper.update_model_from_entity(None, object())  # type: ignore[arg-type]
    assert res1 is None

    # None entity → model inchangé
    res2 = EntityMapper.update_model_from_entity(model, None) # pyright: ignore[reportArgumentType]
    assert res2 is model
    assert model.id == 1
    assert model.name == "Initial"


def test_update_model_from_entity_updates_only_mapper_fields():
    class FakeModel:
        __mapper__ = FakeMapper(keys=["id", "name"])

        def __init__(self, id, name):
            self.id = id
            self.name = name
            self.other = "model-field"

    class Entity:
        def __init__(self):
            self.id = 99
            self.name = "Updated"
            self.other = "entity-field"

    model = FakeModel(id=1, name="Old")
    entity = Entity()

    updated_model = EntityMapper.update_model_from_entity(model, entity) # pyright: ignore[reportArgumentType]

    assert updated_model is model
    assert model.id == 99
    assert model.name == "Updated"
    # "other" n'est pas dans mapper.attrs → ne doit pas être écrasé
    assert model.other == "model-field"


# ---------------------------------------------------------------------
# entity_to_dict
# ---------------------------------------------------------------------


def test_entity_to_dict_uses_custom_to_dict_if_available():
    class EntityWithToDict:
        def __init__(self):
            self.id = 1
            self.name = "X"

        def to_dict(self):
            return {"id": self.id, "custom": True}

    e = EntityWithToDict()
    result = EntityMapper.entity_to_dict(e)

    assert result == {"id": 1, "custom": True}


def test_entity_to_dict_default_behavior_excludes_private_fields():
    class Simple:
        def __init__(self):
            self.id = 5
            self.name = "John"
            self._cache = "hidden"
            self.__very_private = "very-hidden"

    e = Simple()
    result = EntityMapper.entity_to_dict(e)

    assert result["id"] == 5
    assert result["name"] == "John"
    # les champs commençant par "_" sont exclus
    assert "_cache" not in result
    # le name-mangling produit un champ _Simple__very_private dans __dict__,
    # qui commence aussi par "_" → exclu
    assert not any(k.startswith("_") for k in result.keys())
