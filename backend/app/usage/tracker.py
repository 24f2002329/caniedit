import os
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.models.plan import Plan
from app.db.models.subscription import Subscription
from app.db.models.tool import ToolDefinition
from app.db.models.usage import Usage
from app.db.models.user import User
from app.subscriptions.plans import DEFAULT_PLAN_SLUG, PLAN_DEFINITIONS

USAGE_WINDOW_SECONDS = int(os.getenv("USAGE_WINDOW_SECONDS", str(60 * 60 * 24)))
USAGE_RETENTION_DAYS = int(os.getenv("USAGE_RETENTION_DAYS", "30"))
ANON_DAILY_LIMIT = int(os.getenv("ANON_DAILY_LIMIT", "10"))
LOGGED_IN_DAILY_LIMIT = int(os.getenv("LOGGED_IN_DAILY_LIMIT", "20"))


def _default_plan_limit() -> int:
    for definition in PLAN_DEFINITIONS:
        if definition.slug == DEFAULT_PLAN_SLUG:
            return definition.daily_merge_limit
    return LOGGED_IN_DAILY_LIMIT


def _daily_window(now: datetime) -> tuple[datetime, datetime]:
    start = datetime(year=now.year, month=now.month, day=now.day)
    end = start + timedelta(days=1)
    return start, end


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


def _get_tool_definition(db: Session, tool: str) -> ToolDefinition | None:
    return db.query(ToolDefinition).filter(ToolDefinition.slug == tool).first()


def _get_tool_weight(db: Session, tool: str) -> int:
    definition = _get_tool_definition(db, tool)
    if definition and definition.weight > 0:
        return definition.weight
    return 1


def _get_usage_record(
    db: Session,
    tool: str,
    limit: int,
    user_id=None,
    anon_key: str | None = None,
    window_seconds: int = USAGE_WINDOW_SECONDS,
) -> Usage:
    now = datetime.utcnow()
    window_start, window_end = _daily_window(now)
    query = db.query(Usage).filter(
        Usage.tool == tool,
        Usage.period_start == window_start,
        Usage.period_end == window_end,
    )
    if user_id is not None:
        query = query.filter(Usage.user_id == user_id)
    else:
        query = query.filter(Usage.anon_key == anon_key)

    record: Usage | None = query.order_by(Usage.period_end.desc()).first()

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
        anon_key=anon_key,
        tool=tool,
        period_start=window_start,
        period_end=window_end,
        used=0,
        limit_value=limit,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _normalize_ip(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return "unknown"
    if cleaned.startswith("[") and "]" in cleaned:
        bracket_end = cleaned.find("]")
        return cleaned[1:bracket_end] or "unknown"
    if ":" in cleaned:
        last_colon = cleaned.rfind(":")
        host_part = cleaned[:last_colon]
        port_part = cleaned[last_colon + 1 :]
        if host_part and port_part.isdigit() and "." in host_part:
            return host_part
    return cleaned


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return _normalize_ip(forwarded.split(",")[0])
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return _normalize_ip(real_ip)
    if request.client and request.client.host:
        return _normalize_ip(request.client.host)
    return "unknown"


def increment_usage(
    db: Session,
    request: Request,
    user: User | None,
    tool: str,
    amount: int | None = None,
    window_seconds: int = USAGE_WINDOW_SECONDS,
) -> Usage:
    definition = _get_tool_definition(db, tool)
    if definition and definition.is_premium:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="This tool is available on paid plans. Please sign in and upgrade.",
            )
        plan = _get_active_plan(db, user.id)
        if not plan or plan.slug == DEFAULT_PLAN_SLUG:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="This tool is available on paid plans. Please upgrade.",
            )

    if amount is None:
        amount = _get_tool_weight(db, tool)
    if user:
        plan = _get_active_plan(db, user.id)
        limit = plan.daily_merge_limit if plan else LOGGED_IN_DAILY_LIMIT
        record = _get_usage_record(
            db,
            tool=tool,
            limit=limit,
            user_id=user.id,
            window_seconds=window_seconds,
        )
    else:
        anon_key = f"anon:{client_ip(request)}"
        record = _get_usage_record(
            db,
            tool=tool,
            limit=ANON_DAILY_LIMIT,
            anon_key=anon_key,
            window_seconds=window_seconds,
        )

    if record.used + amount > record.limit_value:
        detail = (
            "Daily limit reached. Sign in to get higher limits."
            if not user
            else "Daily limit reached for your plan. Upgrade to increase limits."
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)

    record.used += amount
    record.touch(datetime.utcnow())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def cleanup_usage_rows(db: Session) -> int:
    cutoff = datetime.utcnow() - timedelta(days=USAGE_RETENTION_DAYS)
    deleted = (
        db.query(Usage)
        .filter(Usage.period_end < cutoff)
        .delete(synchronize_session=False)
    )
    if deleted:
        db.commit()
    return deleted or 0


def cleanup_anonymous_usage_rows(db: Session) -> int:
    today_start, _ = _daily_window(datetime.utcnow())
    deleted = (
        db.query(Usage)
        .filter(Usage.anon_key.isnot(None), Usage.period_end <= today_start)
        .delete(synchronize_session=False)
    )
    if deleted:
        db.commit()
    return deleted or 0


def cleanup_usage_rows_loop(session_factory, sleep_seconds: int = 6 * 60 * 60) -> None:
    import time

    while True:
        try:
            with session_factory() as db:
                cleanup_usage_rows(db)
                cleanup_anonymous_usage_rows(db)
        except Exception:
            pass
        time.sleep(sleep_seconds)
