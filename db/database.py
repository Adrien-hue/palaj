# db/database.py
from __future__ import annotations
import os
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from db.base import Base


# ----------------------------------------------------------------------
# Base ORM globale
# ----------------------------------------------------------------------

class SQLiteDatabase:
    """
    Gestionnaire centralisé de base SQLite avec SQLAlchemy.
    Fournit :
      - Création automatique du répertoire DB
      - Sessions transactionnelles
      - Profiling et statistiques globales
      - Contexte sûr d'utilisation via `with`
    """

    def __init__(
        self,
        db_path: str = "data/planning.db",
        echo: bool = False,
        debug: bool = True,
        future: bool = True,
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=echo,
            future=future,
            connect_args={"check_same_thread": False},
        )

        self.SessionLocal = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        self.debug = debug

        # Stats d'activité
        self.stats = {
            "calls": 0,
            "queries": 0,
            "time_total": 0.0,
            "last_query_time": 0.0,
            "operations": defaultdict(int),
        }

        self._attach_sql_listeners()

        if self.debug:
            print(f"SQLiteDatabase Engine initialisé ({self.db_path})")

    # ----------------------------------------------------------------------
    # Gestion de session
    # ----------------------------------------------------------------------
    def get_session(self) -> Session:
        """Retourne une session SQLAlchemy."""
        return self.SessionLocal()

    def session_scope(self):
        """
        Fournit un contexte sûr d'utilisation :
        >>> with db.session_scope() as session:
        >>>     session.add(obj)
        """
        class SessionManager:
            def __init__(self, db: SQLiteDatabase):
                self.db = db
                self.session: Optional[Session] = None

            def __enter__(self):
                self.session = self.db.get_session()
                return self.session

            def __exit__(self, exc_type, exc_val, exc_tb):
                if not self.session:
                    return

                try:
                    if exc_type:
                        self.session.rollback()
                    else:
                        self.session.commit()
                finally:
                    self.session.close()

        return SessionManager(self)

    def safe_commit(self, session: Session):
        """Commit sécurisé, rollback automatique en cas d'échec."""
        try:
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    # ----------------------------------------------------------------------
    # SQL Hooks et profilage
    # ----------------------------------------------------------------------
    def _attach_sql_listeners(self):
        """Ajoute des hooks SQLAlchemy pour mesurer les requêtes réelles."""

        @event.listens_for(self.engine, "before_cursor_execute")
        def before_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault("query_start_time", []).append(time.perf_counter())

        @event.listens_for(self.engine, "after_cursor_execute")
        def after_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.perf_counter() - conn.info["query_start_time"].pop(-1)
            self.stats["queries"] += 1
            self.stats["last_query_time"] = total
            self.stats["time_total"] += total
            if self.debug:
                print(f"[SQL] {total*1000:.2f} ms | {statement.strip()[:80]}")

    # ----------------------------------------------------------------------
    # Profil interne (opérations haut niveau)
    # ----------------------------------------------------------------------
    def _measure(self, op_name: str, func, *args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.perf_counter() - start
            self.stats["calls"] += 1
            self.stats["operations"][op_name] += 1
            self.stats["time_total"] += duration
            if self.debug:
                print(f"[DB] {op_name.upper():<10} | {duration*1000:.2f} ms")

    # ----------------------------------------------------------------------
    # Création & maintenance
    # ----------------------------------------------------------------------
    def create_schema(self):
        """Crée toutes les tables à partir du modèle Base."""
        from db import models

        Base.metadata.create_all(self.engine)
        if self.debug:
            print(f"Base SQLite initialisée à {self.db_path}")

    def drop_schema(self):
        """Supprime toutes les tables."""
        from db import models

        Base.metadata.drop_all(self.engine)
        if self.debug:
            print(f"Base SQLite supprimée ({self.db_path})")

    # ----------------------------------------------------------------------
    # Statistiques & résumé
    # ----------------------------------------------------------------------
    def get_stats(self):
        """Retourne quelques statistiques de base sur la base de données."""
        size_kb = os.path.getsize(self.db_path) / 1024 if os.path.exists(self.db_path) else 0
        return {
            "db_path": self.db_path,
            "db_size_kb": round(size_kb, 2),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(self.db_path)).isoformat()
            if os.path.exists(self.db_path)
            else None,
        }

    def print_stats(self):
        stats = self.get_stats()
        print(f"\nDatabase Stats:")
        for k, v in stats.items():
            print(f"  - {k}: {v}")

    def summary(self) -> str:
        """Retourne un résumé formaté des stats DB."""
        avg_time = (self.stats["time_total"] / self.stats["calls"]) if self.stats["calls"] else 0
        ops = ", ".join(f"{k}: {v}" for k, v in self.stats["operations"].items())
        return (
            f" /---------------------------------------\\ \n"
            f"<========= SQLite Database Stats =========>\n"
            f" \\---------------------------------------/\n"
            f"Database path     : {self.db_path}\n"
            f"Total SQL queries : {self.stats['queries']}\n"
            f"Total calls       : {self.stats['calls']}\n"
            f"Total time        : {self.stats['time_total']:.4f}s\n"
            f"Average time/call : {avg_time*1000:.2f} ms\n"
            f"Last query time   : {self.stats['last_query_time']*1000:.2f} ms\n"
            f"Operations breakdown: {ops or '—'}\n"
            f"------------------------------------------"
        )

    def print_summary(self):
        print(self.summary())