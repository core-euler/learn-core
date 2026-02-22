from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from .usage_entities import UserUsage

DAILY_LIMIT = 30


def check_and_increment_usage(db: Session, user_id: str) -> tuple[bool, str | None]:
    today = datetime.now(timezone.utc).date()
    usage = db.execute(select(UserUsage).where(UserUsage.user_id == user_id)).scalar_one_or_none()
    if not usage:
        usage = UserUsage(user_id=user_id, total_requests=0, requests_today=0, last_request_date=today)
        db.add(usage)
        db.commit()
        db.refresh(usage)

    if usage.last_request_date != today:
        usage.requests_today = 0
        usage.last_request_date = today

    if usage.requests_today >= DAILY_LIMIT:
        db.commit()
        return False, "daily_limit_exceeded"

    usage.requests_today += 1
    usage.total_requests += 1
    usage.updated_at = datetime.now(timezone.utc)
    db.commit()
    return True, None
