from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


a_engine = create_engine(DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=a_engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    from .models import User  # noqa: F401

    Base.metadata.create_all(bind=a_engine)
