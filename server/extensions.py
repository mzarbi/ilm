from typing import Optional
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine


DB_PATH = Path("./data/cib.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def make_sqlite_engine(path: Path) -> Engine:
    engine = create_engine(
        f"sqlite:///{path.as_posix()}",
        future=True,
        pool_pre_ping=True,
        # needed if your app uses threads (Flask dev server/hot reload)
        connect_args={"check_same_thread": False},
    )

    # Enforce FKs + make SQLite more concurrency-friendly (WAL)
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")       # enforce FK constraints
        cursor.execute("PRAGMA journal_mode=WAL;")      # better concurrent reads
        cursor.execute("PRAGMA synchronous=NORMAL;")    # reasonable perf/durability
        cursor.close()

    return engine

ENGINE = make_sqlite_engine(DB_PATH)
Base = declarative_base()