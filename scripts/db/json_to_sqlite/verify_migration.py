# scripts/db/verify_migration.py
import os
import json
from db import db
from db.repositories import (
    agent_repo,
    poste_repo,
    tranche_repo,
    regime_repo,
    affectation_repo,
    etat_jour_agent_repo,
    qualification_repo,
)

# ============================================================
# 🔹 Vérification simple des volumes JSON / SQL
# ============================================================

def count_json_files(folder_path: str) -> int:
    """Compte le nombre de fichiers JSON valides dans un dossier."""
    if not os.path.exists(folder_path):
        return 0
    return len([f for f in os.listdir(folder_path) if f.endswith(".json")])

def verify_table(json_dir: str, repo, label: str):
    """Compare le nombre de fichiers JSON et le nombre de lignes SQLite."""
    json_count = count_json_files(json_dir)
    sql_count = repo.count()

    print(f"🗂️ {label:<20} | JSON: {json_count:<5} | SQL: {sql_count:<5}", end="")

    if json_count == sql_count:
        print(" ✅ OK")
    elif json_count == 0 and sql_count > 0:
        print(" ⚠️ (Pas de JSON source, mais données SQL présentes)")
    else:
        diff = sql_count - json_count
        print(f" ❌ Écart de {diff} enregistrements")


# ============================================================
# 🔹 Vérification d’intégrité des relations
# ============================================================

def check_foreign_key_integrity():
    """Vérifie la cohérence des relations agent/poste/tranche."""
    print("\n🔗 Vérification de l’intégrité des relations clés étrangères :")

    all_agents = {a.id for a in agent_repo.list_all()}
    all_postes = {p.id for p in poste_repo.list_all()}
    all_tranches = {t.id for t in tranche_repo.list_all()}

    orphan_affectations = [
        a for a in affectation_repo.list_all() if a.agent_id not in all_agents or a.tranche_id not in all_tranches
    ]
    orphan_etats = [
        e for e in etat_jour_agent_repo.list_all() if e.agent_id not in all_agents
    ]
    orphan_qualifications = [
        q for q in qualification_repo.list_all()
        if q.agent_id not in all_agents or q.poste_id not in all_postes
    ]

    if not orphan_affectations and not orphan_etats and not orphan_qualifications:
        print("✅ Aucune donnée orpheline détectée !")
    else:
        if orphan_affectations:
            print(f"❌ {len(orphan_affectations)} affectations orphelines trouvées")
        if orphan_etats:
            print(f"❌ {len(orphan_etats)} états journaliers orphelins trouvés")
        if orphan_qualifications:
            print(f"❌ {len(orphan_qualifications)} qualifications orphelines trouvées")


# ============================================================
# 🔹 Vérification des doublons (sur les champs uniques)
# ============================================================

def check_duplicates():
    """Cherche les doublons potentiels (par champ unique logique)."""
    print("\n🔁 Vérification des doublons :")

    # Exemple 1 : agents par nom + prénom
    agents = agent_repo.list_all()
    seen = set()
    dups = []
    for a in agents:
        key = (a.nom.lower(), a.prenom.lower())
        if key in seen:
            dups.append(f"{a.prenom} {a.nom}")
        else:
            seen.add(key)

    if dups:
        print(f"⚠️ {len(dups)} doublons d’agents détectés :")
        for d in dups[:5]:
            print("  →", d)
    else:
        print("✅ Aucun doublon détecté dans les agents.")

    # Exemple 2 : postes par nom
    postes = poste_repo.list_all()
    seen = set()
    dup_postes = [p.nom for p in postes if p.nom in seen or seen.add(p.nom)]
    if dup_postes:
        print(f"⚠️ {len(dup_postes)} doublons dans les postes : {dup_postes}")
    else:
        print("✅ Aucun doublon dans les postes.")


# ============================================================
# 🔹 Échantillons de données pour validation visuelle
# ============================================================

def verify_random_samples(repo, n=3):
    """Affiche quelques enregistrements pour validation manuelle."""
    records = repo.list_all()[:n]
    for r in records:
        print("  →", r)
    if not records:
        print("  (aucune donnée)")

def print_samples():
    print("\n📊 Échantillon de vérification :\n")
    print("👤 Agents :")
    verify_random_samples(agent_repo)
    print("\n🏢 Postes :")
    verify_random_samples(poste_repo)
    print("\n🧩 Tranches :")
    verify_random_samples(tranche_repo)
    print("\n🎓 Qualifications :")
    verify_random_samples(qualification_repo)
    print("\n🕐 États journaliers :")
    verify_random_samples(etat_jour_agent_repo)


# ============================================================
# 🔹 Lancement principal
# ============================================================

def main():
    print("\n🧭 Vérification complète de la migration JSON → SQLite\n")

    base_dir = "data"
    checks = [
        ("agents", agent_repo, os.path.join(base_dir, "agents")),
        ("postes", poste_repo, os.path.join(base_dir, "postes")),
        ("tranches", tranche_repo, os.path.join(base_dir, "tranches")),
        ("regimes", regime_repo, os.path.join(base_dir, "regimes")),
        ("affectations", affectation_repo, os.path.join(base_dir, "affectations")),
        ("états journaliers", etat_jour_agent_repo, os.path.join(base_dir, "etat_jour_agents")),
        ("qualifications", qualification_repo, os.path.join(base_dir, "qualifications")),
    ]

    print("📦 Comparaison JSON ↔ SQL :\n")
    for label, repo, folder in checks:
        verify_table(folder, repo, label)

    check_foreign_key_integrity()
    check_duplicates()
    print_samples()

    print("\n✅ Vérification terminée.\n")


if __name__ == "__main__":
    main()
