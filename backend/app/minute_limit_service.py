from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from .rate_limit_entities import UserRateWindow

MINUTE_LIMIT = 20
WINDOW_SECONDS = 60


def check_minute_limit(db: Session, user_id: str) -> tuple[bool, str | None]:
    now = int(datetime.now(timezone.utc).timestamp())
    window_start = now - (now % WINDOW_SECONDS)

    rw = db.execute(select(UserRateWindow).where(UserRateWindow.user_id == user_id)).scalar_one_or_none()
    if not rw:
        rw = UserRateWindow(user_id=user_id, window_start_epoch=window_start, requests_in_window=0)
        db.add(rw)
        db.commit()
        db.refresh(rw)

    if rw.window_start_epoch != window_start:
        rw.window_start_epoch = window_start
        rw.requests_in_window = 0

    if rw.requests_in_window >= MINUTE_LIMIT:
        db.commit()
        return False, "minute_rate_limited"

    rw.requests_in_window += 1
    rw.updated_at = datetime.now(timezone.utc)
    db.commit()
    return True, None
