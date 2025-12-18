# scripts/db/inspect_db.py
import argparse
from sqlalchemy import inspect, text

from db.database import SQLiteDatabase


def inspect_database(db: SQLiteDatabase, table: str | None = None, sample_rows: int = 5):
    """Affiche un aperçu global de la base SQLite et de ses tables."""
    print(f"\n🔍 Inspection de la base : {db.db_path}\n")

    # --- 1️⃣ Infos générales sur la base ---
    stats = db.get_stats()
    print("📊 STATISTIQUES GLOBALES :")
    for k, v in stats.items():
        print(f"  • {k}: {v}")
    print("\n" + "-" * 60)

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if not tables:
        print("⚠️  Aucune table trouvée. (Base vide ?)")
        return

    # --- 2️⃣ Si une table spécifique est demandée ---
    if table:
        if table not in tables:
            print(f"❌ Table '{table}' introuvable. Tables disponibles : {', '.join(tables)}")
            return
        tables = [table]

    # --- 3️⃣ Parcours des tables ---
    with db.get_session() as session:
        for table_name in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0
            print(f"\n📘 Table: {table_name} ({count} lignes)")

            if count > 0:
                query = text(f"SELECT * FROM {table_name} LIMIT {sample_rows}")
                rows = session.execute(query).fetchall()
                for row in rows:
                    print(f"  → {dict(row._mapping)}")
            else:
                print("  (aucune donnée)")

    print("\n" + "-" * 60)
    print("✅ Inspection terminée.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Inspecte la base SQLite et affiche un aperçu des tables et de leur contenu."
    )
    parser.add_argument(
        "--table",
        type=str,
        help="Nom d'une table spécifique à inspecter (ex: agent, tranche, affectation)."
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=5,
        help="Nombre de lignes à afficher par table (défaut: 5)."
    )
    parser.add_argument(
        "--db",
        type=str,
        default="data/planning.db",
        help="Chemin vers la base SQLite (défaut: data/planning.db)."
    )

    args = parser.parse_args()

    db = SQLiteDatabase(args.db, debug=False)
    inspect_database(db, table=args.table, sample_rows=args.sample)


if __name__ == "__main__":
    main()
