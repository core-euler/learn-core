from dataclasses import dataclass, field
from typing import Dict, Optional

from .models import User, Session


@dataclass
class InMemoryStore:
    users: Dict[str, User] = field(default_factory=dict)
    users_by_email: Dict[str, str] = field(default_factory=dict)
    sessions: Dict[str, Session] = field(default_factory=dict)
    refresh_index: Dict[str, str] = field(default_factory=dict)
    used_refresh_hashes: set[str] = field(default_factory=set)

    def add_user(self, user: User) -> None:
        self.users[user.id] = user
        if user.email:
            self.users_by_email[user.email] = user.id

    def get_user_by_email(self, email: str) -> Optional[User]:
        user_id = self.users_by_email.get(email)
        return self.users.get(user_id) if user_id else None

    def add_session(self, session: Session) -> None:
        self.sessions[session.id] = session
        self.refresh_index[session.refresh_token_hash] = session.id

    def get_session_by_refresh_hash(self, refresh_hash: str) -> Optional[Session]:
        sid = self.refresh_index.get(refresh_hash)
        return self.sessions.get(sid) if sid else None

    def revoke_session(self, session: Session) -> None:
        session.is_revoked = True
        self.used_refresh_hashes.add(session.refresh_token_hash)

    def revoke_all_for_user(self, user_id: str) -> None:
        for session in self.sessions.values():
            if session.user_id == user_id and not session.is_revoked:
                self.revoke_session(session)


store = InMemoryStore()
