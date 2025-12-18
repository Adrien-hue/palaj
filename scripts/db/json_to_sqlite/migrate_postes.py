# scripts/db/json_to_sqlite/migrate_postes.py
import json
import os
from db.database import SQLiteDatabase
from db.repositories.poste_repo import PosteRepository


def migrate_postes(json_dir="data/postes"):
    poste_repo = PosteRepository()

    count = 0
    for fname in os.listdir(json_dir):
        if not fname.endswith(".json"):
            continue

        with open(os.path.join(json_dir, fname), "r", encoding="utf-8") as f:
            data = json.load(f)

        poste_data = {"id": data["id"], "nom": data["nom"]}
        poste_repo.upsert(poste_data)
        count += 1

    print(f"✅ Migration terminée : {count} postes importés depuis {json_dir}")


if __name__ == "__main__":
    migrate_postes()
