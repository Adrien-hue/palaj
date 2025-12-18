# scripts/db/backup_db.py
import os
import shutil
from datetime import datetime
import argparse

BACKUP_DIR = "backups"


# ==========================================================
# == Sauvegarde
# ==========================================================
def backup_sqlite(db_path: str):
    """Crée une copie horodatée de la base SQLite dans le dossier /backups."""
    if not os.path.exists(db_path):
        print(f"❌ Base SQLite introuvable à l'emplacement : {db_path}")
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = os.path.basename(db_path)
    backup_filename = f"{db_name.replace('.db', '')}_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    shutil.copy2(db_path, backup_path)
    print(f"✅ Sauvegarde créée : {backup_path}")
    return backup_path


# ==========================================================
# == Liste des sauvegardes
# ==========================================================
def list_backups():
    """Liste toutes les sauvegardes existantes."""
    if not os.path.exists(BACKUP_DIR):
        print("⚠️  Aucun dossier de sauvegarde trouvé.")
        return []

    backups = sorted(os.listdir(BACKUP_DIR))
    if not backups:
        print("ℹ️  Aucune sauvegarde disponible.")
        return []

    print("\n📦 Sauvegardes disponibles :")
    for file in backups:
        path = os.path.join(BACKUP_DIR, file)
        size_kb = os.path.getsize(path) / 1024
        modified = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
        print(f" - {file} ({size_kb:.1f} KB, {modified})")
    return backups


# ==========================================================
# == Restauration d'une sauvegarde
# ==========================================================
def restore_backup(db_path: str, backup_filename: str):
    """Restaure une sauvegarde spécifique vers la base principale."""
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    if not os.path.exists(backup_path):
        print(f"❌ Sauvegarde introuvable : {backup_path}")
        return

    if os.path.exists(db_path):
        confirm = input(f"⚠️  La base {db_path} existe déjà. Écraser ? (o/n) : ").lower()
        if confirm != "o":
            print("❌ Opération annulée.")
            return

    shutil.copy2(backup_path, db_path)
    print(f"✅ Base restaurée depuis : {backup_path}")
    print(f"📍 Destination : {db_path}")


# ==========================================================
# == CLI principale
# ==========================================================
def main():
    parser = argparse.ArgumentParser(description="Sauvegarde, restauration ou inspection des sauvegardes SQLite.")
    parser.add_argument(
        "--db",
        type=str,
        default="data/planning.db",
        help="Chemin de la base SQLite principale (défaut: data/planning.db)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Affiche la liste des sauvegardes existantes."
    )
    parser.add_argument(
        "--restore",
        type=str,
        help="Nom d'une sauvegarde à restaurer (ex: planning_backup_20251105_224223.db)"
    )

    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.restore:
        restore_backup(args.db, args.restore)
    else:
        backup_sqlite(args.db)


if __name__ == "__main__":
    main()