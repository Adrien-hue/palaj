# db/mappers/entity_mapper.py
from datetime import date, datetime, time
import inspect
from typing import Any, cast, Optional, Type, TypeVar
from sqlalchemy.orm import attributes, DeclarativeBase, InstanceState, Mapper

# Import centralisé des entités du domaine
from core.domain.entities import *

# Types génériques
TModel = TypeVar("TModel")
TEntity = TypeVar("TEntity")

_PRIMITIVE_TYPES = (int, float, bool, str, bytes, date, datetime, time)

class EntityMapper:
    """
    Convertisseur bidirectionnel entre :
    - les modèles SQLAlchemy (infrastructure)
    - les entités métier (domaine)
    """

    # =========================================================
    # 🔹 MODELE → ENTITÉ
    # =========================================================
    @staticmethod
    def model_to_entity(model: Any, entity_class: Type[TEntity]) -> Optional[TEntity]:
        """
        Convertit un modèle SQLAlchemy en entité métier en:
        - collectant les colonnes/relations disponibles
        - filtrant selon les paramètres du __init__ de l'entité
        - mappant les relations → champs *_id si nécessaire
        - peuplant les caches privés (_relation) si présents
        """
        if model is None:
            return None

        # 1) Conversion custom si présente
        if hasattr(model, "to_entity") and callable(model.to_entity):
            ent = model.to_entity()
            if not isinstance(ent, entity_class):
                raise TypeError(f"Expected {entity_class.__name__}, got {type(ent).__name__}")
            return ent

        # 2) Extraire données via le mapper SQLAlchemy
        data: dict[str, Any] = {}
        mapper: Optional[Mapper] = getattr(model, "__mapper__", None)
        if mapper is not None:
            # -> colonnes + relations
            for attr in mapper.attrs.keys():
                try:
                    value = getattr(model, attr)
                except Exception:
                    continue
                data[attr] = value
        else:
            # fallback (rare)
            data = {k: v for k, v in vars(model).items() if not k.startswith("_")}

        # 3) Déterminer les champs acceptés par l'entité via __init__
        sig = inspect.signature(entity_class.__init__)
        ctor_params = {name for name, p in sig.parameters.items() if name != "self"}

        # 4) Construire le payload pour l'entité
        payload: dict[str, Any] = {}

        # a) Colonnes « simples » qui matchent le ctor
        for k, v in data.items():
            if k in ctor_params and isinstance(v, _PRIMITIVE_TYPES):
                payload[k] = v

        # b) Relations → xxx_id si l'entité attend xxx_id et que relation a un .id
        for k, v in data.items():
            rel_id_field = f"{k}_id"
            if rel_id_field in ctor_params and v is not None and hasattr(v, "id"):
                try:
                    payload[rel_id_field] = getattr(v, "id")
                except Exception:
                    pass

        # c) Si l'entité accepte directement le champ (rare), et que la valeur est « primitive »
        for k, v in data.items():
            if k in ctor_params and k not in payload and isinstance(v, _PRIMITIVE_TYPES):
                payload[k] = v

        # 5) Instancier l'entité
        entity = entity_class(**payload)

        # 6) Renseigner les caches privés pour relations chargées (ex: _regime)
        #    On tente un mapping récursif relation->entité si disponible.
        for k, v in data.items():
            private_cache_name = f"_{k}"
            if hasattr(entity, private_cache_name) and v is not None:
                # Essayer de résoudre la classe d'entité cible à partir du nom (k)
                # Exemple: relation 'regime' -> entité 'Regime' dans core.domain.entities
                entity_type_name = k.capitalize()
                target_entity_cls = getattr(__import__("core.domain.entities", fromlist=[entity_type_name]), entity_type_name, None)
                if target_entity_cls is not None:
                    try:
                        nested_entity = EntityMapper.model_to_entity(v, target_entity_cls)
                        setattr(entity, private_cache_name, nested_entity)
                    except Exception:
                        # si échec, on ignore – ce cache est optionnel
                        pass

        return entity

    # =========================================================
    # 🔹 ENTITÉ → MODELE
    # =========================================================
    @staticmethod
    def entity_to_model(entity: Any, model_class: Type[DeclarativeBase]) -> Any:
        """
        Convertit une entité métier vers un modèle SQLAlchemy.

        :param entity: instance d'entité métier
        :param model_class: classe SQLAlchemy correspondante
        """
        if entity is None:
            return None

        data = entity.__dict__.copy()
        valid_fields = set(model_class.__mapper__.attrs.keys())  # typé OK
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return model_class(**filtered_data)

    # =========================================================
    # 🔹 MISE À JOUR
    # =========================================================
    @staticmethod
    def update_model_from_entity(model: DeclarativeBase, entity: Any) -> DeclarativeBase:
        """
        Met à jour un modèle SQLAlchemy existant à partir d'une entité.
        """
        if model is None or entity is None:
            return model

        valid_fields = set(model.__mapper__.attrs.keys())
        for k, v in vars(entity).items():
            if k in valid_fields:
                setattr(model, k, v)
        return model

    # =========================================================
    # 🔹 UTILITAIRE : ENTITÉ → DICT
    # =========================================================
    @staticmethod
    def entity_to_dict(entity: Any) -> dict[str, Any]:
        """
        Convertit une entité en dict brut (utile pour logs ou API).
        """
        if hasattr(entity, "to_dict") and callable(entity.to_dict):
            return cast(dict[str, Any], entity.to_dict())

        return {
            k: v for k, v in vars(entity).items()
            if not k.startswith("_")
        }
