from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Subscription(Base):
	__tablename__ = "subscriptions"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
	plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), index=True, nullable=False)
	status = Column(String(40), index=True, nullable=False, default="active")
	current_period_start = Column(DateTime, nullable=True)
	current_period_end = Column(DateTime, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

	plan = relationship("Plan")

	def touch(self, now: datetime) -> None:
		self.updated_at = now
