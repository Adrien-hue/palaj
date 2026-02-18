# db/database.py
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from db.base import Base


class Database:
    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        debug: bool = False,
        future: bool = True,
    ):
        self.database_url = database_url
        self.debug = debug

        engine_kwargs: dict[str, Any] = {
            "echo": echo,
            "future": future,
            "pool_pre_ping": True,
        }

        # SQLite specific connect args (sinon Postgres n'aime pas)
        if database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}

        self.engine = create_engine(database_url, **engine_kwargs)

        self.SessionLocal = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        self.stats = {
            "calls": 0,
            "queries": 0,
            "time_total": 0.0,
            "last_query_time": 0.0,
            "operations": defaultdict(int),
        }

        self._attach_sql_listeners()

        if self.debug:
            print(f"Database Engine initialisé ({self.database_url})")

    def get_session(self) -> Session:
        return self.SessionLocal()

    def session_scope(self):
        class SessionManager:
            def __init__(self, db: Database):
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
        try:
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    def _attach_sql_listeners(self):
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