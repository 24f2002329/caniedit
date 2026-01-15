import os
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.plan import Plan
from app.db.models.subscription import Subscription
from app.db.models.usage import Usage
from app.db.models.user import User
from app.subscriptions.plans import DEFAULT_PLAN_SLUG, PLAN_DEFINITIONS

USAGE_WINDOW_SECONDS = int(os.getenv("USAGE_WINDOW_SECONDS", str(60 * 60 * 24)))


def _default_plan_limit() -> int:
    for definition in PLAN_DEFINITIONS:
        if definition.slug == DEFAULT_PLAN_SLUG:
            return definition.daily_merge_limit
    return 30


def _get_active_plan(db: Session, user_id) -> Plan | None:
    subscription: Subscription | None = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.current_period_end.desc().nullslast())
        .first()
    )
    if subscription:
        plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        if plan:
            return plan
    return db.query(Plan).filter(Plan.slug == DEFAULT_PLAN_SLUG).first()


def _get_usage_record(
    db: Session,
    user_id,
    tool: str,
    limit: int,
    window_seconds: int = USAGE_WINDOW_SECONDS,
) -> Usage:
    now = datetime.utcnow()
    window_end = now + timedelta(seconds=window_seconds)
    record: Usage | None = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.tool == tool, Usage.period_end > now)
        .order_by(Usage.period_end.desc())
        .first()
    )

    if record:
        if record.limit_value != limit:
            record.limit_value = limit
            record.touch(now)
            db.add(record)
            db.commit()
            db.refresh(record)
        return record

    record = Usage(
        user_id=user_id,
        tool=tool,
        period_start=now,
        period_end=window_end,
        used=0,
        limit_value=limit,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def increment_usage(
    db: Session,
    user: User,
    tool: str,
    amount: int = 1,
    window_seconds: int = USAGE_WINDOW_SECONDS,
) -> Usage:
    plan = _get_active_plan(db, user.id)
    limit = plan.daily_merge_limit if plan else _default_plan_limit()
    record = _get_usage_record(db, user.id, tool=tool, limit=limit, window_seconds=window_seconds)

    if record.used + amount > record.limit_value:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily limit reached for your plan. Upgrade to increase limits.",
        )

    record.used += amount
    record.touch(datetime.utcnow())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
