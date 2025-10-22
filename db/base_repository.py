import os
import json
from datetime import datetime
from typing import List, Optional, TypeVar, Generic, Type

from db import cache_manager
from db.database import JsonDatabase

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, db: JsonDatabase, collection_name: str, cls: Type[T]):
        """
        Classe de base pour un repository JSON avec cache et suivi.
        :param db: instance JsonDatabase
        :param collection_name: nom du dossier/collection
        :param cls: classe de l'objet (Agent, Poste, etc.)
        """
        self.db = db
        self.collection = collection_name
        self.cls = cls
        self._cache: dict[str, T] = {}  # clé = id
        self.cache_manager = cache_manager

    # ---------- Helpers ----------
    def _get_folder_path(self) -> str:
        """Renvoie le chemin du dossier de la collection."""
        return os.path.join(self.db.base_dir, self.collection)

    def _make_cache_key(self, key: str) -> str:
        """Génère une clé unique par collection pour éviter les collisions globales."""
        return f"{self.collection}:{key}"
    
    # ---------- CACHE ----------
    def _cache_get(self, key: str) -> T | None:
        full_key = self._make_cache_key(key)
        obj = self._cache.get(full_key)
        cls_name = self.cls.__name__
        if obj:
            self.cache_manager.register_hit(cls_name)
        else:
            self.cache_manager.register_miss(cls_name)
        return obj

    def _cache_set(self, key: str, obj: T):
        full_key = self._make_cache_key(key)
        if full_key not in self._cache:
            self._cache[full_key] = obj
            self.cache_manager.track(obj)

    def _cache_delete(self, key: str):
        full_key = self._make_cache_key(key)
        if full_key in self._cache:
            del self._cache[full_key]

    # ---------- CRUD ----------
    def create(self, obj: T):
        key = self._get_key(obj)
        self.db.create(self.collection, key, self._serialize(obj))
        self._cache_set(key, obj)

    def get(self, key: int | str) -> T | None:
        """
        Récupère un objet depuis le cache ou la base JSON.
        :param key: identifiant numérique de l'objet
        :return: instance de la classe T, ou None si non trouvé
        """
        obj = self._cache_get(str(key))
        if obj:
            return obj

        data = self.db.get(self.collection, key)
        if not data:
            return None

        obj = self._deserialize(data)

        self._cache_set(str(key), obj)

        return obj


    def list_all(self) -> List[T]:
        if self._cache:
            return list(self._cache.values())

        all_data = self.db.list_all(self.collection)
        objects = []
        for key, data in all_data.items():
            obj = self._deserialize(data)
            self._cache_set(key, obj)
            objects.append(obj)
        return objects

    def update(self, obj: T):
        key = self._get_key(obj)
        self.db.update(self.collection, key, self._serialize(obj))
        self._cache_set(key, obj)

    def delete(self, obj: T):
        key = self._get_key(obj)
        self.db.delete(self.collection, key)
        self._cache_delete(key)

    # ---------- SERIALIZATION ----------
    def _get_key(self, obj: T) -> str:
        """
        Définit la clé utilisée dans le JSON.
        Par défaut, on utilise l'attribut 'id'.
        """
        return str(getattr(obj, "id"))

    def _serialize(self, obj: T) -> dict:
        """À redéfinir dans chaque repository spécifique si besoin"""
        raise NotImplementedError

    def _deserialize(self, data: dict) -> T:
        """À redéfinir dans chaque repository spécifique si besoin"""
        raise NotImplementedError

    def export_to_single_file(self, suffix: Optional[str] = None) -> str:
        """
        Regroupe tous les fichiers JSON individuels en un seul fichier.
        Ex: data/backups/affectations_full_2025-10-20_162300.json
        """
        folder = self._get_folder_path()
        if not os.path.exists(folder):
            raise FileNotFoundError(f"Dossier non trouvé : {folder}")

        # Collecter toutes les données
        all_data = []
        for fname in os.listdir(folder):
            if fname.endswith(".json"):
                with open(os.path.join(folder, fname), "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        all_data.append(data)
                    except json.JSONDecodeError as e:
                        print(f"[⚠️] Erreur de lecture : {fname} ({e})")

        # Fichier de sortie
        backup_dir = os.path.join(self.db.base_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        base_name = os.path.basename(folder)
        export_name = f"{base_name}_full_{timestamp}"
        if suffix:
            export_name += f"_{suffix}"
        export_path = os.path.join(backup_dir, export_name + ".json")

        # Sauvegarde
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)

        print(f"[📦] Export complet : {len(all_data)} enregistrements → {export_path}")
        return export_path

    # ============================================================
    # 🔹 Import complet : re-split à partir d’un fichier global
    # ============================================================
    def import_from_single_file(self, file_path: str, overwrite: bool = False):
        """
        Restaure tous les enregistrements à partir d’un fichier unique JSON.
        Chaque objet est réécrit dans un fichier individuel.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fichier d’import non trouvé : {file_path}")

        folder = self._get_folder_path()
        os.makedirs(folder, exist_ok=True)

        # Backup de sécurité avant modification
        if not overwrite:
            self.export_to_single_file("before_import")

        # Charger les données
        with open(file_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)

        count = 0
        for obj_data in all_data:
            obj = self._deserialize(obj_data)
            if obj:
                key = self._get_key(obj)
                file_name = f"{key}.json"
                file_path = os.path.join(folder, file_name)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(obj_data, f, indent=2, ensure_ascii=False)
                count += 1

        print(f"[🪄] Import terminé : {count} fichiers restaurés dans {folder}")