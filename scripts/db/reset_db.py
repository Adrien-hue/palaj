# scripts/db/reset_db.py
import argparse
import os
from db.database import SQLiteDatabase


def reset_database(db_path: str, debug: bool = False, force: bool = False):
    print(f"⚠️  Réinitialisation complète de la base de données : {db_path}")

    if os.path.exists(db_path):
        if not force:
            confirm = input(f"❗ Le fichier existe déjà. Voulez-vous le supprimer ? (o/n) : ").lower()
            if confirm != "o":
                print("❌ Opération annulée.")
                return
        os.remove(db_path)
        print("🗑️  Ancien fichier SQLite supprimé.")

    db = SQLiteDatabase(db_path, debug=debug)
    db.create_schema()

    db.print_stats()
    print("✅ Base de données recréée avec succès !")


def main():
    parser = argparse.ArgumentParser(description="Réinitialise la base de données SQLite.")
    parser.add_argument(
        "--db",
        type=str,
        default="data/planning.db",
        help="Chemin vers la base SQLite (défaut: data/planning.db)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Active le mode debug (affiche les opérations)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force la réinitialisation sans confirmation."
    )

    args = parser.parse_args()
    reset_database(args.db, args.debug, args.force)

if __name__ == "__main__":
    main()