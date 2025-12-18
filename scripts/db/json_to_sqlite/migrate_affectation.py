# scripts/db/json_to_sqlite/migrate_affectations.py
import json
import os
from datetime import date

from db.database import SQLiteDatabase
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.agent_repo import AgentRepository
from db.repositories.tranche_repo import TrancheRepository


def migrate_affectations(json_dir="data/affectations"):
    print("🔧 Migration des affectations vers SQLite...")

    affectation_repo = AffectationRepository()
    agent_repo = AgentRepository()
    tranche_repo = TrancheRepository()

    count_ok = 0
    count_ignored = 0

    for fname in os.listdir(json_dir):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(json_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vérifie les champs essentiels
        if not all(k in data for k in ["agent_id", "tranche_id", "jour"]):
            print(f"[⚠️] Fichier {fname} ignoré (champs manquants).")
            count_ignored += 1
            continue

        # Vérifie que l’agent existe
        agent = agent_repo.get(data["agent_id"])
        if not agent:
            print(f"[⚠️] Agent ID={data['agent_id']} introuvable — affectation ignorée.")
            count_ignored += 1
            continue

        # Vérifie que la tranche existe
        tranche = tranche_repo.get(data["tranche_id"])
        if not tranche:
            print(f"[⚠️] Tranche ID={data['tranche_id']} introuvable — affectation ignorée.")
            count_ignored += 1
            continue

        # Conversion de la date
        try:
            jour = date.fromisoformat(data["jour"])
        except ValueError:
            print(f"[⚠️] Date invalide pour {fname} : {data['jour']}")
            count_ignored += 1
            continue

        # Création / mise à jour
        affectation_data = {
            "agent_id": data["agent_id"],
            "tranche_id": data["tranche_id"],
            "jour": jour,
        }

        affectation_repo.upsert(affectation_data, unique_field="jour")
        print(
            f"✅ Affectation {agent.prenom} {agent.nom} → Tranche {tranche.nom} ({jour})"
        )
        count_ok += 1

    print(f"\n✅ Migration terminée : {count_ok} affectations importées, {count_ignored} ignorées.")


if __name__ == "__main__":
    migrate_affectations()
