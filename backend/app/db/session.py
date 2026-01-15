import os
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from dotenv import load_dotenv

from app.db.base import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL or SUPABASE_DATABASE_URL must be set for PostgreSQL.")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
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

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    Base.metadata.create_all(bind=engine)

    from app.subscriptions.plans import seed_default_plans

    with SessionLocal() as db:
        seed_default_plans(db)
