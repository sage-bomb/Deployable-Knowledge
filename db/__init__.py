"""Database setup and connection helpers.

This module provides the SQLAlchemy engine and session factory used by the
project.  It is currently unused by the application code but will serve as the
foundation for migrating file-based persistence to a real database.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

def init_db() -> None:
    """Create database tables for all defined models."""
    from . import models  # noqa: F401  # ensure model registration

    Base.metadata.create_all(bind=engine)
