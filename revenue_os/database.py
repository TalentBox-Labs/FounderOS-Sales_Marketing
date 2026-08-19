from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from revenue_os.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create missing tables from canonical SQLAlchemy metadata.

    Idempotent: existing tables are left in place. Does not drop, seed,
    migrate, or mutate environment.
    """
    import revenue_os.models  # noqa: F401 — register models on Base.metadata
    from revenue_os.models.base import Base

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
