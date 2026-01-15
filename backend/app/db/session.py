import os
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_PATH = BACKEND_DIR / "data" / "app.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")


def _normalize_sqlite_url(url: str) -> str:
    if not url.startswith("sqlite:///"):
        return url
    path = url.replace("sqlite:///", "", 1)
    candidate = Path(path)
    if candidate.is_absolute():
        return url
    resolved = BACKEND_DIR / candidate
    return f"sqlite:///{resolved}"


def _ensure_sqlite_directory(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    path = url.replace("sqlite:///", "", 1)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


DATABASE_URL = _normalize_sqlite_url(DATABASE_URL)
_ensure_sqlite_directory(DATABASE_URL)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Iterator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables if they do not exist."""
    from app.db import models  # noqa: F401 - registers models with metadata

    Base.metadata.create_all(bind=engine)
