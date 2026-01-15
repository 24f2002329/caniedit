"""Compatibility shim for the legacy app.db module.

Prefer importing from app.db.session or app.db.base in new code.
"""

from app.db.base import Base
from app.db.session import DATABASE_URL, SessionLocal, engine, get_db, init_db

__all__ = [
    "Base",
    "DATABASE_URL",
    "SessionLocal",
    "engine",
    "get_db",
    "init_db",
]
