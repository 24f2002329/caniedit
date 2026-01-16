"""User-related business logic."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from app.db.models.plan import Plan
from app.db.models.subscription import Subscription
from app.db.models.usage import Usage
from app.db.models.user import User

DELETE_GRACE_DAYS = 30


def get_profile(user: User) -> dict:
	return {
		"id": str(user.id),
		"email": user.email,
		"full_name": user.full_name,
		"delete_requested_at": user.delete_requested_at.isoformat() if user.delete_requested_at else None,
		"deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
	}


def update_profile(db: Session, user: User, full_name: str | None = None, email: str | None = None) -> User:
	updated = False
	if full_name is not None and full_name != user.full_name:
		user.full_name = full_name
		updated = True
	if email is not None and email != user.email:
		user.email = email
		updated = True
	if updated:
		user.touch(datetime.utcnow())
		db.add(user)
		db.commit()
		db.refresh(user)
	return user


def request_account_deletion(db: Session, user: User) -> dict:
	if user.delete_requested_at:
		delete_at = user.delete_requested_at + timedelta(days=DELETE_GRACE_DAYS)
		return {
			"delete_requested_at": user.delete_requested_at,
			"delete_at": delete_at,
		}

	now = datetime.utcnow()
	user.delete_requested_at = now
	user.touch(now)
	db.add(user)
	db.commit()
	db.refresh(user)

	return {
		"delete_requested_at": user.delete_requested_at,
		"delete_at": user.delete_requested_at + timedelta(days=DELETE_GRACE_DAYS),
	}


def _daily_window(now: datetime) -> tuple[datetime, datetime]:
	start = datetime(year=now.year, month=now.month, day=now.day)
	end = start + timedelta(days=1)
	return start, end


def get_usage_summary(db: Session, user: User) -> list[dict]:
	now = datetime.utcnow()
	window_start, window_end = _daily_window(now)
	rows: Iterable[Usage] = (
		db.query(Usage)
		.filter(
			Usage.user_id == user.id,
			Usage.period_start == window_start,
			Usage.period_end == window_end,
			Usage.used > 0,
		)
		.order_by(Usage.used.desc())
		.all()
	)
	return [
		{
			"tool": row.tool,
			"used": row.used,
			"limit": row.limit_value,
			"period_end": row.period_end.isoformat(),
		}
		for row in rows
	]


def get_subscription_summary(db: Session, user: User) -> dict:
	subscription = (
		db.query(Subscription)
		.filter(Subscription.user_id == user.id, Subscription.status == "active")
		.order_by(Subscription.current_period_end.desc().nullslast())
		.first()
	)
	plan = None
	if subscription:
		plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()

	plans = db.query(Plan).order_by(Plan.name.asc()).all()
	return {
		"active": {
			"status": subscription.status if subscription else None,
			"plan": {
				"id": str(plan.id),
				"slug": plan.slug,
				"name": plan.name,
				"daily_limit": plan.daily_merge_limit,
			} if plan else None,
			"current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
		} if subscription else None,
		"plans": [
			{
				"id": str(p.id),
				"slug": p.slug,
				"name": p.name,
				"daily_limit": p.daily_merge_limit,
			}
			for p in plans
		],
	}


def cleanup_deleted_users(db: Session) -> int:
	cutoff = datetime.utcnow() - timedelta(days=DELETE_GRACE_DAYS)
	to_delete = (
		db.query(User)
		.filter(User.delete_requested_at.isnot(None), User.delete_requested_at < cutoff)
		.all()
	)
	count = 0
	for user in to_delete:
		count += 1
		db.delete(user)
	if count:
		db.commit()
	return count


def cleanup_deleted_users_loop(session_factory, sleep_seconds: int = 6 * 60 * 60) -> None:
	import time

	while True:
		try:
			with session_factory() as db:
				cleanup_deleted_users(db)
		except Exception:
			pass
		time.sleep(sleep_seconds)


__all__ = [
	"get_profile",
	"update_profile",
	"request_account_deletion",
	"get_usage_summary",
	"get_subscription_summary",
	"cleanup_deleted_users_loop",
]
