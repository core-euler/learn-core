from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid


@dataclass
class User:
    id: str
    email: Optional[str]
    password_hash: Optional[str]
    first_name: str
    auth_method: str
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Session:
    id: str
    user_id: str
    refresh_token_hash: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


def new_user(email: Optional[str], password_hash: Optional[str], first_name: str, auth_method: str) -> User:
    return User(id=str(uuid.uuid4()), email=email, password_hash=password_hash, first_name=first_name, auth_method=auth_method)


def new_session(user_id: str, refresh_token_hash: str, days: int = 30) -> Session:
    return Session(
        id=str(uuid.uuid4()),
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=days),
    )
