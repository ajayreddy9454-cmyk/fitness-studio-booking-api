"""Database configuration and session management with SQLAlchemy and SQLite.

Provides the declarative base for models and a FastAPI dependency
for obtaining a scoped database session per request.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# For SQLite, check_same_thread=False allows FastAPI worker threads
# to use the same database connection across concurrent requests safely.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True if SQL query debugging is needed
)

# SessionLocal is a factory for new SQLAlchemy Session objects
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all SQLAlchemy ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request.

    Ensures the session is always closed properly when the request completes,
    preventing connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
