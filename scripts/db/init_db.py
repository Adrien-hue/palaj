# scripts/db/init_db.py
import argparse
from db.database import SQLiteDatabase


def init_database(db_path: str, debug: bool = False):
    print(f"🔧 Initialisation de la base de données SQLite ({db_path})...")

    db = SQLiteDatabase(db_path, debug=debug)
    db.create_schema()

    db.print_stats()
    print("✅ Base initialisée avec succès !")


def main():
    parser = argparse.ArgumentParser(description="Initialise la base de données SQLite.")
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

    args = parser.parse_args()
    init_database(args.db, args.debug)


if __name__ == "__main__":
    main()
