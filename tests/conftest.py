# tests/conftest.py
import os
import tempfile
import pytest
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

# Import your app factory and globals
from app import create_app
from app.extensions import Base
import app.models_cib as m  # ensure all models are registered on Base


def make_sqlite_engine(db_path: Path | None = None) -> Engine:
    url = f"sqlite:///{db_path.as_posix()}" if db_path else "sqlite+pysqlite:///:memory:"
    engine = create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.close()

    return engine


@pytest.fixture(scope="session")
def engine() -> Engine:
    # Use a temp file DB for the test session (faster than in-memory with multiple connections)
    tmp = Path(tempfile.gettempdir()) / "cib_test.sqlite"
    if tmp.exists():
        tmp.unlink()
    eng = make_sqlite_engine(tmp)
    # Create schema once for all tests
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def app(engine: Engine):
    # Build a fresh app bound to the session engine
    app = create_app(engine)

    # Optionally set testing config flags
    app.config["TESTING"] = True

    # Seed minimal reference data + a couple of entities/projects for each test
    with Session(engine) as s, s.begin():
        # Refs (idempotent upserts via merge)
        s.merge(m.PraActivity(code="buyout", label="Buyout"))
        s.merge(m.CounterpartyType(code="bank", label="Bank"))
        s.merge(m.Currency(code="EUR", name="Euro"))
        s.merge(m.Country(iso2="FR", iso3="FRA", name="France"))
        s.merge(m.Sector(code="FIN", label="Financials", description="Financial sector"))

        # Entities
        sponsor = m.LegalEntity(
            rmpm_code="SPN001", rmpm_type="INTERNAL", name="Sponsor SA"
        )
        cpty = m.LegalEntity(
            rmpm_code="CPTY01", rmpm_type="INTERNAL", name="Counterparty Ltd"
        )
        s.add_all([sponsor, cpty])
        s.flush()

        # Project
        proj = m.Project(name="Project Neptune", code="NEP", description="Test project")
        s.add(proj)

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def post_json(client, url, payload, expected_status=201):
    rv = client.post(url, json=payload)
    assert rv.status_code == expected_status, rv.get_json()
    return rv
