from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "db" / "schema.sql"


def make_engine(database_url: str | None = None) -> Engine:
    url = database_url or settings.database_url
    kwargs: dict[str, object] = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def ensure_schema(target_engine: Engine = engine) -> None:
    """Apply the package SQL schema to an empty or existing SQLite database."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with target_engine.begin() as connection:
        raw = getattr(connection.connection, "driver_connection", connection.connection)
        if hasattr(raw, "executescript"):
            raw.executescript(sql)
        else:  # pragma: no cover - retained for non-SQLite development engines
            for statement in sql.split(";"):
                if statement.strip():
                    connection.exec_driver_sql(statement)
        connection.execute(text("PRAGMA foreign_keys = ON"))


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
