# scripts/db/json_to_sqlite/migrate_tranches.py
import json
import os
from datetime import time

from db.database import SQLiteDatabase
from db.repositories.tranche_repo import TrancheRepository
from db.repositories.poste_repo import PosteRepository


def migrate_tranches(json_dir="data/tranches"):
    print("🔧 Migration des tranches horaires vers SQLite...")

    tranche_repo = TrancheRepository()
    poste_repo = PosteRepository()

    count_ok = 0
    count_ignored = 0

    for fname in os.listdir(json_dir):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(json_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vérification des champs essentiels
        if not all(k in data for k in ["nom", "heure_debut", "heure_fin"]):
            print(f"[⚠️] Fichier {fname} ignoré (champs manquants).")
            count_ignored += 1
            continue

        # Recherche du poste lié (si renseigné)
        poste = None
        if "poste" in data and data["poste"] is not None:
            poste_id = data["poste"]
            postes = poste_repo.get(poste_id)
            if postes:
                poste = postes.id
            else:
                print(f"[⚠️] Poste '{poste_id}' introuvable — tranche ignorée.")
                count_ignored += 1
                continue
        else:
            print(f"[⚠️] Aucune référence poste dans {fname} — tranche ignorée.")
            print(data)
            count_ignored += 1
            continue

        # Conversion des heures au format Python
        try:
            heure_debut = time.fromisoformat(data["heure_debut"])
            heure_fin = time.fromisoformat(data["heure_fin"])
        except Exception as e:
            print(f"[❌] Erreur conversion heure pour {data['nom']}: {e}")
            count_ignored += 1
            continue

        # Insertion / mise à jour
        tranche_data = {
            "id": data.get("id"),
            "nom": data["nom"],
            "heure_debut": heure_debut,
            "heure_fin": heure_fin,
            "poste_id": poste,
        }

        tranche_repo.upsert(tranche_data)
        print(f"✅ Tranche '{data['nom']}' importée (poste_id={poste}).")
        count_ok += 1

    print(f"\n✅ Migration terminée : {count_ok} tranches importées, {count_ignored} ignorées.")


if __name__ == "__main__":
    migrate_tranches()
