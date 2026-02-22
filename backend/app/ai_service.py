from sqlalchemy import select
from sqlalchemy.orm import Session

from .ai_entities import AiSession
from .course_entities import UserLessonProgress, UserModuleProgress


LESSON_MODES = {"lecture", "exam"}


def ensure_mode_access(db: Session, user_id: str, mode: str, lesson_id: str | None) -> tuple[bool, str | None]:
    if mode in LESSON_MODES:
        if not lesson_id:
            return False, "lesson_required"
        lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.lesson_id == lesson_id)).scalar_one_or_none()
        if not lp or lp.status == "locked":
            return False, "lesson_locked"
        return True, None

    if mode == "consultant":
        completed_modules = db.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == user_id, UserModuleProgress.status == "completed")).scalars().all()
        if not completed_modules:
            return False, "consultant_locked"
        return True, None

    return False, "invalid_mode"


def create_ai_session(db: Session, user_id: str, mode: str, lesson_id: str | None, exam_rubric: str | None = None) -> AiSession:
    s = AiSession(user_id=user_id, mode=mode, lesson_id=lesson_id, exam_rubric=exam_rubric)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s
