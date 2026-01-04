import os
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")


def _ensure_sqlite_directory(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    path = url.replace("sqlite:///", "", 1)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


_ensure_sqlite_directory(DATABASE_URL)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def get_db() -> Iterator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables if they do not exist."""
    from app import models  # noqa: F401 - registers models with metadata

    Base.metadata.create_all(bind=engine)
