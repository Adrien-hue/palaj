# scripts/db/json_to_sqlite/migrate_agents.py
import json
import os

from db.repositories.agent_repo import AgentRepository
from db.repositories.regime_repo import RegimeRepository


def migrate_agents(json_dir="data/agents"):
    print("🔧 Migration des agents vers SQLite...")

    agent_repo = AgentRepository()
    regime_repo = RegimeRepository()

    count_ok = 0
    count_ignored = 0
    count_unknown = 0

    for fname in os.listdir(json_dir):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(json_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vérifie la présence des champs essentiels
        if not all(k in data for k in ["nom", "prenom", "regime_id"]):
            print(f"[⚠️] Fichier {fname} ignoré (champs manquants).")
            count_ignored += 1
            continue

        # Vérifie que le régime existe
        regime = regime_repo.get(data["regime_id"])
        if not regime:
            print(f"[⚠️] Régime ID={data['regime_id']} introuvable.")
            count_unknown += 1
            regime_id = None
        else :
            regime_id = data["regime_id"]

        # Prépare les données d'agent
        agent_data = {
            "id": data.get("id"),
            "nom": data["nom"],
            "prenom": data["prenom"],
            "code_personnel": data.get("code_personnel", ""),
            "regime_id": regime_id,
        }

        agent_repo.upsert(agent_data)
        print(f"✅ Agent {data['prenom']} {data['nom']} importé (régime={regime_id}).")
        count_ok += 1

    print(f"\n✅ Migration terminée : {count_ok} agents importés, {count_ignored} ignorés, {count_unknown} inconnus.")


if __name__ == "__main__":
    migrate_agents()
