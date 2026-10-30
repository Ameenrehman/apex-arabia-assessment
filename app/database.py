"""Database connection and session lifecycle management using SQLAlchemy.

Supports PostgreSQL in production and SQLite in testing/development environments.
"""

from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

# Determine database engine settings
db_url = settings.get_database_url
connect_args = {}

# SQLite-specific configuration for tests
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine = create_engine(db_url, connect_args=connect_args)
else:
    # PostgreSQL production configuration with connection pooling
    engine = create_engine(
        db_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # Automatically detect and recover dropped connections
        pool_recycle=1800,   # Recycle connections after 30 minutes
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency generator that provides a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """Executes a lightweight query to verify active database connectivity.

    Used by the readiness probe (/health/ready).
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db() -> None:
    """Creates database tables defined in Base metadata."""
    Base.metadata.create_all(bind=engine)
