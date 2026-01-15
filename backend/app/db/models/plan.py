from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    daily_merge_limit = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def touch(self, now: datetime) -> None:
        self.updated_at = now
