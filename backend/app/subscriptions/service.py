"""Subscription logic."""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.plan import Plan
from app.db.models.subscription import Subscription
from app.db.models.user import User
from app.subscriptions.plans import DEFAULT_PLAN_SLUG


def ensure_starter_subscription(db: Session, user: User) -> Subscription:
	"""Ensure a user has at least one subscription (starter by default)."""
	existing = (
		db.query(Subscription)
		.filter(Subscription.user_id == user.id)
		.order_by(Subscription.created_at.desc())
		.first()
	)
	if existing:
		return existing

	plan = db.query(Plan).filter(Plan.slug == DEFAULT_PLAN_SLUG).first()
	if not plan:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Starter plan is not configured",
		)

	now = datetime.utcnow()
	subscription = Subscription(
		user_id=user.id,
		plan_id=plan.id,
		status="active",
		current_period_start=now,
		current_period_end=None,
	)
	db.add(subscription)
	db.commit()
	db.refresh(subscription)
	return subscription


__all__ = ["ensure_starter_subscription"]
