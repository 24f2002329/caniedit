import os
from datetime import datetime, timedelta
from typing import Tuple

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.models.usage import UsageCounter
from app.db.models.user import User

ANON_DAILY_LIMIT = int(os.getenv("ANON_DAILY_LIMIT", "10"))
USER_DAILY_LIMIT = int(os.getenv("USER_DAILY_LIMIT", "30"))
USAGE_WINDOW_SECONDS = int(os.getenv("USAGE_WINDOW_SECONDS", str(60 * 60 * 24)))


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def usage_key_and_limit(request: Request, user: User | None) -> Tuple[str, str, int]:
    if user:
        return ("user", f"user:{user.id}", USER_DAILY_LIMIT)
    return ("anon", f"anon:{client_ip(request)}", ANON_DAILY_LIMIT)


def get_usage_counter(
    db: Session,
    scope: str,
    key: str,
    limit: int,
    window_seconds: int = USAGE_WINDOW_SECONDS,
) -> UsageCounter:
    now = datetime.utcnow()
    window_end = now + timedelta(seconds=window_seconds)
    counter: UsageCounter | None = db.query(UsageCounter).filter(UsageCounter.key == key).first()

    if counter and counter.window_end > now:
        updated = False
        if counter.limit != limit:
            counter.limit = limit
            updated = True
        if counter.scope != scope:
            counter.scope = scope
            updated = True
        if updated:
            counter.touch(now)
            db.add(counter)
            db.commit()
            db.refresh(counter)
        return counter

    if counter:
        counter.window_start = now
        counter.window_end = window_end
        counter.used = 0
        counter.limit = limit
        counter.scope = scope
        counter.touch(now)
        db.add(counter)
    else:
        counter = UsageCounter(
            key=key,
            scope=scope,
            window_start=now,
            window_end=window_end,
            used=0,
            limit=limit,
        )
        db.add(counter)
    db.commit()
    db.refresh(counter)
    return counter


def increment_usage(
    db: Session,
    request: Request,
    user: User | None,
    amount: int = 1,
    window_seconds: int = USAGE_WINDOW_SECONDS,
) -> UsageCounter:
    scope, key, limit = usage_key_and_limit(request, user)
    counter = get_usage_counter(db, scope=scope, key=key, limit=limit, window_seconds=window_seconds)

    if counter.used + amount > counter.limit:
        detail = "Daily limit reached. Sign in to get 2x more merges and save history." if scope == "anon" else "Daily limit reached. Upgrade for higher limits."
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)

    counter.used += amount
    counter.touch(datetime.utcnow())
    db.add(counter)
    db.commit()
    db.refresh(counter)
    return counter
