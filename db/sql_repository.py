# db/sql_repository.py
from typing import Any, Generic, TypeVar, Type, List, Literal, Optional, Sequence

from sqlalchemy.orm import DeclarativeBase, selectinload, joinedload

from db.database import SQLiteDatabase
from core.adapters.entity_mapper import EntityMapper

TModel = TypeVar("TModel", bound=DeclarativeBase)
TEntity = TypeVar("TEntity")

LoadStrategy = Literal["selectin", "joined", "none"]

class SQLRepository(Generic[TModel, TEntity]):
    """
    Classe de base générique pour les repositories SQLAlchemy.
    Elle fournit un ensemble de méthodes CRUD ainsi qu'un mapping automatique
    entre les modèles ORM (infrastructure) et les entités métier (domaine).

    ---
    ⚙️ Paramètres génériques :
      • TModel  : Classe SQLAlchemy (ex: AgentModel)
      • TEntity : Classe d'entité métier correspondante (ex: AgentEntity)
    """

    def __init__(self, db: SQLiteDatabase, model_class: Type[TModel], entity_class: Type[TEntity]):
        """
        Initialise un repository SQL.

        :param db: Instance active de la base SQLiteDatabase (contient engine et sessions)
        :param model_class: Classe SQLAlchemy utilisée pour les opérations ORM
        :param entity_class: Classe d'entité métier retournée aux couches supérieures
        """
        self.db = db
        self.model_class: Type[TModel] = model_class
        self.entity_class: Type[TEntity] = entity_class

    # =========================================================
    # 🔹 MÉTHODES "MODEL" INTERNES (infrastructure)
    # =========================================================
    def _apply_eager_loading(self, query, eager_relations: Optional[Sequence[str]], strategy: LoadStrategy):
        """
        Applique dynamiquement une stratégie de préchargement (eager loading)
        sur une requête SQLAlchemy.

        :param query: L'objet Query SQLAlchemy à enrichir
        :param eager_relations: Liste de relations à charger (ex: ["regime", "poste.tranches"])
        :param strategy:
            - "selectin" → charge chaque relation via des requêtes séparées (efficace pour gros volumes)
            - "joined"   → charge les relations via des jointures SQL (efficace sur peu de lignes)
            - "none"     → n'applique aucun préchargement
        :return: La requête enrichie avec les options de chargement
        """
        if not eager_relations or strategy == "none":
            return query

        strategy_map = {
            "selectin": selectinload,
            "joined": joinedload,
        }
        try:
            loader = strategy_map[strategy]
        except KeyError:
            raise ValueError(
                f"strategy inconnu: {strategy}. "
                f"Utiliser: {', '.join(strategy_map.keys())}"
            )

        for rel in eager_relations:
            # Autoriser "regime" (str) ou AgentModel.regime (attribut)
            if isinstance(rel, str):
                try:
                    attr = getattr(self.model_class, rel)
                except AttributeError as e:
                    raise ValueError(
                        f"Relation '{rel}' introuvable sur {self.model_class.__name__}"
                    ) from e
            else:
                # supposé être un attribut lié à la classe (InstrumentedAttribute)
                attr = rel

            query = query.options(loader(attr))

        return query
    
    def _default_order_by(self) -> Sequence[Any]:
        """
        Hook overrideable par repo enfant.
        Retourne un ou plusieurs critères SQLAlchemy pour order_by().
        """
        if hasattr(self.model_class, "id"):
            return (getattr(self.model_class, "id"),)
        return ()
    
    def get_model(
        self,
        object_id: int,
        eager_relations: Optional[Sequence[str]] = None,
        load_strategy: LoadStrategy = "selectin",
    ) -> Optional[TModel]:
        """
        Récupère un modèle SQLAlchemy directement depuis la base.

        :param object_id: Identifiant unique de la ligne à charger
        :param eager_relations: Liste optionnelle de relations à précharger (ex: ["regime"])
        :param load_strategy: Méthode de préchargement ("selectin", "joined", ou "none")
        :return: Le modèle SQLAlchemy correspondant ou None si non trouvé

        ---
        💡 Exemple :
        ```python
        model = agent_repo.get_model(1, eager_relations=["regime"], load_strategy="joined")
        ```
        """
        with self.db.session_scope() as session:
            query = session.query(self.model_class).filter_by(id=object_id)
            query = self._apply_eager_loading(query, eager_relations, load_strategy)
            return query.one_or_none()

    def list_all_models(
        self,
        eager_relations: Optional[Sequence[str]] = None,
        load_strategy: LoadStrategy = "selectin",
    ) -> List[TModel]:
        return self.list_models(limit=None, offset=0, eager_relations=eager_relations, load_strategy=load_strategy)
        
    def list_models(
        self,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
        eager_relations: Optional[Sequence[str]] = None,
        load_strategy: LoadStrategy = "selectin",
        order_by=None,
    ) -> List[TModel]:
        """
        Liste paginée des modèles ORM.
        - limit=None => pas de limite (retourne tout)
        - offset par défaut 0
        """
        if offset < 0:
            raise ValueError("offset doit être >= 0")
        if limit is not None and limit < 0:
            raise ValueError("limit doit être >= 0 ou None")

        with self.db.session_scope() as session:
            query = session.query(self.model_class)
            query = self._apply_eager_loading(query, eager_relations, load_strategy)

            if order_by is None:
                default_order = self._default_order_by()
                if default_order:
                    query = query.order_by(*default_order)
            else:
                # accepte: un critère unique ou une séquence
                if isinstance(order_by, (list, tuple)):
                    query = query.order_by(*order_by)
                else:
                    query = query.order_by(order_by)

            if offset:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return query.all()

    # =========================================================
    # 🔹 MÉTHODES "ENTITY" (niveau domaine)
    # =========================================================
    def get(
        self,
        object_id: int,
        eager_relations: Optional[Sequence[str]] = None,
        load_strategy: LoadStrategy = "selectin",
    ) -> Optional[TEntity]:
        """
        Récupère une entité métier à partir de son ID.

        - Ouvre une session temporaire
        - Précharge les relations demandées
        - Convertit le modèle ORM en entité Python pure (détachée)
        - Ferme la session avant le retour

        :param object_id: ID de l'entité recherchée
        :param eager_relations: Relations à charger (ex: ["regime"])
        :param load_strategy: Type de préchargement à utiliser ("selectin", "joined" ou "none")
        :return: Instance d'entité métier ou None si absente

        ---
        💡 Exemple :
        ```python
        agent = agent_repo.get(1, eager_relations=["regime"])
        print(agent.nom, agent.regime.nom)
        ```
        """
        model = self.get_model(object_id, eager_relations=eager_relations, load_strategy=load_strategy)
        if not model:
            return None
        return EntityMapper.model_to_entity(model, self.entity_class)

    def list_all(
        self,
        eager_relations: Optional[Sequence[str]] = None,
        load_strategy: LoadStrategy = "selectin",
    ) -> List[TEntity]:
        """
        Retourne toutes les entités métier depuis la base,
        avec un préchargement optionnel des relations.

        - Charge les modèles ORM dans une session temporaire
        - Applique la stratégie de chargement choisie
        - Convertit chaque modèle en entité Python pure (indépendante de SQLAlchemy)
        - Ferme la session avant de retourner le résultat

        :param eager_relations: Liste de relations à charger (ex: ["agent", "agent.regime"])
        :param load_strategy: "selectin", "joined", ou "none"
        :return: Liste d'entités métier prêtes à l'emploi (pas de lazy loading)

        ---
        💡 Exemple :
        ```python
        agents = agent_repo.list_all(eager_relations=["regime"], load_strategy="selectin")
        affectations = affectation_repo.list_all(eager_relations=["agent", "agent.regime"])
        ```
        """
        return self.list(
            limit=None,
            offset=0,
            eager_relations=eager_relations,
            load_strategy=load_strategy,
        )
    
    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
        eager_relations: Optional[Sequence[str]] = None,
        load_strategy: LoadStrategy = "selectin",
        order_by=None,
    ) -> List[TEntity]:
        """
        Liste paginée des entités métier.
        """
        models = self.list_models(
            limit=limit,
            offset=offset,
            eager_relations=eager_relations,
            load_strategy=load_strategy,
            order_by=order_by,
        )
        return [
            e for m in models
            if (e := EntityMapper.model_to_entity(m, self.entity_class)) is not None
        ]

    def create(self, entity: TEntity) -> TEntity:
        """Crée un enregistrement à partir d'une entité."""
        model = EntityMapper.entity_to_model(entity, self.model_class)
        with self.db.session_scope() as session:
            session.add(model)
            session.flush()
            session.refresh(model)
            result = EntityMapper.model_to_entity(model, self.entity_class)
            assert result is not None, "La création doit retourner une entité valide"
            return result

    def update(self, entity: TEntity) -> Optional[TEntity]:
        """Met à jour un enregistrement à partir d'une entité."""
        with self.db.session_scope() as session:
            model = session.get(self.model_class, getattr(entity, "id", None))
            if not model:
                return None
            EntityMapper.update_model_from_entity(model, entity)
            session.add(model)
            session.flush()
            session.refresh(model)
            return EntityMapper.model_to_entity(model, self.entity_class)

    def delete(self, object_id: int) -> bool:
        """Supprime un enregistrement."""
        with self.db.session_scope() as session:
            model = session.get(self.model_class, object_id)
            if not model:
                return False
            session.delete(model)
            return True

    # -------------------------
    # 🔹 UPSERT (insert or update)
    # -------------------------
    def upsert(self, entity: TEntity, unique_field: str = "id") -> TEntity:
        """
        Insère ou met à jour une entité selon un champ unique (par défaut : id).
        """
        entity_data = EntityMapper.entity_to_dict(entity)
        value = entity_data.get(unique_field)

        with self.db.session_scope() as session:
            instance = (
                session.query(self.model_class)
                .filter(getattr(self.model_class, unique_field) == value)
                .first()
            )

            if instance:
                EntityMapper.update_model_from_entity(instance, entity)
            else:
                instance = EntityMapper.entity_to_model(entity, self.model_class)
                session.add(instance)

            session.flush()
            session.refresh(instance)
            result = EntityMapper.model_to_entity(instance, self.entity_class)
            assert result is not None, "L'upsert doit toujours retourner une entité valide"
            return result

    # -------------------------
    # 🔹 Utilitaires
    # -------------------------
    def count(self) -> int:
        """Retourne le nombre total d'enregistrements."""
        with self.db.session_scope() as session:
            return session.query(self.model_class).count()

    def exists(self, **filters) -> bool:
        """Vérifie si un enregistrement existe selon un filtre."""
        with self.db.session_scope() as session:
            return session.query(self.model_class).filter_by(**filters).first() is not None