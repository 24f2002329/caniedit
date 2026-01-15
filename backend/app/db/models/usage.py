from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Usage(Base):
    __tablename__ = "usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    tool = Column(String(100), index=True, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    used = Column(Integer, default=0, nullable=False)
    limit_value = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def touch(self, now: datetime) -> None:
        self.updated_at = now
