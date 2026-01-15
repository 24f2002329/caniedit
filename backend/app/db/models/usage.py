from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class UsageCounter(Base):
    __tablename__ = "usage_counters"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    scope = Column(String(50), nullable=False)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    used = Column(Integer, default=0, nullable=False)
    limit = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def touch(self, now: datetime) -> None:
        self.updated_at = now
