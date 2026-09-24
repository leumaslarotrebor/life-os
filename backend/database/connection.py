"""
LIFE OS — Database connection module.

Provides:
- engine: SQLAlchemy engine (configured via DATABASE_URL env var)
- SessionLocal: session factory for use in API/MCP handlers
- Base: declarative base for all models
- get_db: FastAPI dependency yielding a database session
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./lifeos_dev.db",  # safe local fallback for development only
)

# SQLite requires a special connect_args for thread safety in FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base shared by all LIFE OS models."""
    pass


def get_db():
    """FastAPI dependency: yields a database session and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
