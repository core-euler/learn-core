from sqlalchemy import select
from sqlalchemy.orm import Session

from .entities import User
from .course_entities import Module, Lesson, UserLessonProgress, UserModuleProgress


def bootstrap_progress_for_user(db: Session, user_id: str) -> None:
    ensure_progress_for_user(db, user_id)


def ensure_progress_for_user(db: Session, user_id: str) -> None:
    modules = (
        db.execute(select(Module).where(Module.is_published == True).order_by(Module.order_index.asc())).scalars().all()
    )
    if not modules:
        return

    module_progress = {
        row.module_id: row
        for row in db.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == user_id)).scalars().all()
    }
    for m in modules:
        if m.id not in module_progress:
            db.add(UserModuleProgress(user_id=user_id, module_id=m.id, status="locked"))

    lesson_progress = {
        row.lesson_id: row
        for row in db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id)).scalars().all()
    }
    for m in modules:
        lessons = (
            db.execute(
                select(Lesson)
                .where(Lesson.module_id == m.id, Lesson.is_published == True)
                .order_by(Lesson.order_index.asc())
            )
            .scalars()
            .all()
        )
        for lesson in lessons:
            if lesson.id not in lesson_progress:
                db.add(UserLessonProgress(user_id=user_id, lesson_id=lesson.id, status="locked"))

    db.flush()

    published_module_ids = {m.id for m in modules}
    has_open_module = db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.user_id == user_id,
            UserModuleProgress.module_id.in_(published_module_ids),
            UserModuleProgress.status.in_(["available", "completed"]),
        )
    ).scalars().first()
    if not has_open_module:
        first_module = modules[0]
        first_mp = db.execute(
            select(UserModuleProgress).where(
                UserModuleProgress.user_id == user_id,
                UserModuleProgress.module_id == first_module.id,
            )
        ).scalar_one()
        first_mp.status = "available"

    all_published_lessons = (
        db.execute(select(Lesson).where(Lesson.is_published == True).order_by(Lesson.order_index.asc())).scalars().all()
    )
    published_lesson_ids = {lesson.id for lesson in all_published_lessons}
    has_open_lesson = None
    if published_lesson_ids:
        has_open_lesson = db.execute(
            select(UserLessonProgress).where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id.in_(published_lesson_ids),
                UserLessonProgress.status.in_(["available", "completed"]),
            )
        ).scalars().first()

    if not has_open_lesson and modules:
        first_lesson = (
            db.execute(
                select(Lesson)
                .where(Lesson.module_id == modules[0].id, Lesson.is_published == True)
                .order_by(Lesson.order_index.asc())
            )
            .scalars()
            .first()
        )
        if first_lesson:
            first_lp = db.execute(
                select(UserLessonProgress).where(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson_id == first_lesson.id,
                )
            ).scalar_one()
            first_lp.status = "available"

    db.commit()


def ensure_progress_for_all_users(db: Session) -> None:
    user_ids = db.execute(select(User.id)).scalars().all()
    for user_id in user_ids:
        ensure_progress_for_user(db, user_id)


def complete_lesson_and_unlock_next(db: Session, user_id: str, lesson_id: str) -> None:
    lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.lesson_id == lesson_id)).scalar_one()
    lp.status = "completed"

    lesson = db.execute(select(Lesson).where(Lesson.id == lesson_id)).scalar_one()
    lessons = db.execute(select(Lesson).where(Lesson.module_id == lesson.module_id, Lesson.is_published == True).order_by(Lesson.order_index.asc())).scalars().all()
    idx = [x.id for x in lessons].index(lesson_id)

    if idx + 1 < len(lessons):
        next_lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.lesson_id == lessons[idx + 1].id)).scalar_one()
        if next_lp.status == "locked":
            next_lp.status = "available"
    else:
        mp = db.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == user_id, UserModuleProgress.module_id == lesson.module_id)).scalar_one()
        mp.status = "completed"

        modules = db.execute(select(Module).where(Module.is_published == True).order_by(Module.order_index.asc())).scalars().all()
        midx = [m.id for m in modules].index(lesson.module_id)
        if midx + 1 < len(modules):
            next_mp = db.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == user_id, UserModuleProgress.module_id == modules[midx + 1].id)).scalar_one()
            if next_mp.status == "locked":
                next_mp.status = "available"
            first_next_lesson = db.execute(select(Lesson).where(Lesson.module_id == modules[midx + 1].id, Lesson.is_published == True).order_by(Lesson.order_index.asc())).scalars().first()
            if first_next_lesson:
                nlp = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.lesson_id == first_next_lesson.id)).scalar_one()
                if nlp.status == "locked":
                    nlp.status = "available"

    db.commit()
