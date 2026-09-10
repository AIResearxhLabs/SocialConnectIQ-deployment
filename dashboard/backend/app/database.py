"""
Database connection and session management (SQLite via SQLAlchemy).

The dashboard uses a local SQLite file so it runs without any external DB.
Production deployments should swap DB_URL to PostgreSQL.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

DB_URL = os.getenv("DASHBOARD_DB_URL", "sqlite:///./dashboard.db")

# SQLite requires connect_args for thread safety when used with FastAPI
_connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_all_tables() -> None:
    """Create all tables (idempotent — safe to call on every startup)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
