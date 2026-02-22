from sqlalchemy import select
from sqlalchemy.orm import Session

from .course_entities import Module, Lesson, UserLessonProgress, UserModuleProgress


def bootstrap_progress_for_user(db: Session, user_id: str) -> None:
    modules = db.execute(select(Module).where(Module.is_published == True).order_by(Module.order_index.asc())).scalars().all()
    if not modules:
        return

    first_module_id = modules[0].id
    for m in modules:
        mp = UserModuleProgress(user_id=user_id, module_id=m.id, status="available" if m.id == first_module_id else "locked")
        db.add(mp)

    for m in modules:
        lessons = db.execute(select(Lesson).where(Lesson.module_id == m.id, Lesson.is_published == True).order_by(Lesson.order_index.asc())).scalars().all()
        for idx, l in enumerate(lessons):
            status = "available" if m.id == first_module_id and idx == 0 else "locked"
            db.add(UserLessonProgress(user_id=user_id, lesson_id=l.id, status=status))

    db.commit()


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
