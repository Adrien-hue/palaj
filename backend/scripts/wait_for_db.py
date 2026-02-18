from __future__ import annotations

import time

from sqlalchemy import create_engine, text

from backend.app.settings import settings


def main() -> None:
    timeout_s = 60
    interval_s = 2
    deadline = time.time() + timeout_s

    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            engine = create_engine(settings.database_url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database is ready")
            return
        except Exception as e:
            last_error = e
            print(f"⏳ Waiting for database... ({e})")
            time.sleep(interval_s)

    raise RuntimeError(f"Database not ready after {timeout_s}s") from last_error


if __name__ == "__main__":
    main()
