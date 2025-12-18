# scripts/db/json_to_sqlite/migrate_etat_jour_agent.py
import json
import os
from datetime import date

from db.database import SQLiteDatabase
from db.repositories.agent_repo import AgentRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository


def migrate_etat_jour_agent(json_dir="data/etat_jour_agents"):
    print("🔧 Migration des états journaliers d’agents vers SQLite...")

    etat_repo = EtatJourAgentRepository()
    agent_repo = AgentRepository()

    count_ok = 0
    count_ignored = 0

    for fname in os.listdir(json_dir):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(json_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not all(k in data for k in ["agent_id", "jour", "type_jour"]):
            print(f"[⚠️] Fichier {fname} ignoré (champs manquants).")
            count_ignored += 1
            continue

        agent = agent_repo.get(data["agent_id"])
        if not agent:
            print(f"[⚠️] Agent ID={data['agent_id']} introuvable — ignoré.")
            count_ignored += 1
            continue

        # Conversion de la date
        try:
            jour = date.fromisoformat(data["jour"])
        except ValueError:
            print(f"[⚠️] Date invalide pour {fname} : {data['jour']}")
            count_ignored += 1
            continue

        etat_data = {
            "agent_id": data["agent_id"],
            "jour": jour,
            "type_jour": data["type_jour"],
            "description": data.get("description", ""),
        }

        etat_repo.upsert(etat_data)
        print(f"✅ {agent.prenom} {agent.nom} — {jour}: {etat_data['type_jour']}")
        count_ok += 1

    print(f"\n✅ Migration terminée : {count_ok} états importés, {count_ignored} ignorés.")


if __name__ == "__main__":
    migrate_etat_jour_agent()
