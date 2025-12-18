# scripts/json_to_sqlite/migrate_regimes.py
import json
import os
from db.repositories.regime_repo import RegimeRepository

SOURCE_DIR = "data/regimes"  # dossier contenant les anciens JSON


def migrate_regimes():
    repo = RegimeRepository()
    count = 0

    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Dossier introuvable : {SOURCE_DIR}")
        return

    for file_name in os.listdir(SOURCE_DIR):
        if not file_name.endswith(".json"):
            continue

        file_path = os.path.join(SOURCE_DIR, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"⚠️ Erreur lecture {file_name}: {e}")
                continue

        # Vérifie que les clés essentielles sont présentes
        if "nom" not in data or "id" not in data:
            print(f"⚠️ Données incomplètes : {file_name}")
            continue

        # Insère ou met à jour le régime
        repo.upsert({
            "id": data["id"],
            "nom": data["nom"],
            "desc": data.get("desc", ""),
            "duree_moyenne_journee_service_min": data.get("duree_moyenne_journee_service_min", 0),
            "repos_periodiques_annuels": data.get("repos_periodiques_annuels", 0),
        })

        count += 1

    print(f"✅ Migration terminée : {count} régimes importés dans SQLite.")


if __name__ == "__main__":
    print("🔄 Démarrage de la migration des régimes...")
    migrate_regimes()
