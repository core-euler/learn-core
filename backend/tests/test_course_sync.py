import os
from pathlib import Path

os.environ['APP_ENV'] = 'test'

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.content_index import default_index_path
from backend.app.course_entities import Module, Lesson, UserModuleProgress, UserLessonProgress
from backend.app.course_sync import sync_course_catalog_from_index
from backend.app.entities import User


client = TestClient(app)


def test_course_sync_populates_catalog_and_progress_for_existing_user():
    client.post('/_test/reset')

    client.post('/api/auth/register', json={'email': 'sync@example.com', 'password': 'password123'})

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == 'sync@example.com')).scalar_one()

        result = sync_course_catalog_from_index(
            db,
            index_path=default_index_path(),
            repo_root=Path(__file__).resolve().parent.parent,
        )

        modules = db.execute(select(Module).where(Module.is_published == True).order_by(Module.order_index.asc())).scalars().all()
        lessons = db.execute(select(Lesson).where(Lesson.is_published == True)).scalars().all()
        user_modules = db.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == user.id)).scalars().all()
        user_lessons = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user.id)).scalars().all()

        assert result['published_modules'] == len(modules) == 2
        assert result['published_lessons'] == len(lessons) == 3
        assert all(module.slug for module in modules)
        assert all(lesson.slug for lesson in lessons)

        assert len(user_modules) == 2
        assert len(user_lessons) == 3
        assert sum(1 for row in user_modules if row.status == 'available') == 1
        assert sum(1 for row in user_lessons if row.status == 'available') == 1
    finally:
        db.close()


def test_course_sync_is_idempotent_by_slug_keys():
    client.post('/_test/reset')

    db = SessionLocal()
    try:
        sync_course_catalog_from_index(
            db,
            index_path=default_index_path(),
            repo_root=Path(__file__).resolve().parent.parent,
        )
        first_modules = {
            row.slug: row.id
            for row in db.execute(select(Module).where(Module.is_published == True)).scalars().all()
        }
        first_lessons = {
            (row.module_id, row.slug): row.id
            for row in db.execute(select(Lesson).where(Lesson.is_published == True)).scalars().all()
        }

        sync_course_catalog_from_index(
            db,
            index_path=default_index_path(),
            repo_root=Path(__file__).resolve().parent.parent,
        )
        second_modules = {
            row.slug: row.id
            for row in db.execute(select(Module).where(Module.is_published == True)).scalars().all()
        }
        second_lessons = {
            (row.module_id, row.slug): row.id
            for row in db.execute(select(Lesson).where(Lesson.is_published == True)).scalars().all()
        }

        assert first_modules == second_modules
        assert first_lessons == second_lessons
    finally:
        db.close()
