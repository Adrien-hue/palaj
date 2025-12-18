# scripts/db/json_to_sqlite/migrate_qualifications.py
import json
import os
from datetime import date

from db.repositories.agent_repo import AgentRepository
from db.repositories.poste_repo import PosteRepository
from db.repositories.qualification_repo import QualificationRepository


def migrate_qualifications(json_dir="data/qualifications"):
    print("🎓 Migration des qualifications vers SQLite...")

    qualif_repo = QualificationRepository()
    agent_repo = AgentRepository()
    poste_repo = PosteRepository()

    count_ok = 0
    count_ignored = 0

    for fname in os.listdir(json_dir):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(json_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not all(k in data for k in ["agent_id", "poste_id"]):
            print(f"[⚠️] Fichier {fname} ignoré (champs manquants)")
            count_ignored += 1
            continue

        agent = agent_repo.get(data["agent_id"])
        poste = poste_repo.get(data["poste_id"])
        if not agent or not poste:
            print(f"[⚠️] Agent ou poste introuvable pour {fname}")
            count_ignored += 1
            continue

        # Conversion date si présente
        date_q = None
        if data.get("date_qualification"):
            try:
                date_q = date.fromisoformat(data["date_qualification"])
            except ValueError:
                print(f"[⚠️] Date invalide dans {fname}: {data['date_qualification']}")

        qualif_repo.upsert(
            {
                "agent_id": data["agent_id"],
                "poste_id": data["poste_id"],
                "date_qualification": date_q,
            }
        )

        print(
            f"✅ Qualification: {agent.prenom} {agent.nom} → {poste.nom} "
            f"({date_q or 'sans date'})"
        )
        count_ok += 1

    print(f"\n🎯 Migration terminée : {count_ok} qualifications importées, {count_ignored} ignorées.")


if __name__ == "__main__":
    migrate_qualifications()
