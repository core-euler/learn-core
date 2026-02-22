from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def setup_user():
    client.post('/_test/reset')
    client.post('/_test/seed-course')
    client.post('/api/auth/register', json={'email': 'p@example.com', 'password': 'password123'})
    l = client.post('/api/auth/login', json={'email': 'p@example.com', 'password': 'password123'})
    return l.cookies.get('access_token')


def test_bootstrap_progress_initial_unlocks():
    access = setup_user()
    r = client.get('/api/progress', cookies={'access_token': access})
    assert r.status_code == 200
    data = r.json()
    assert data['modules_count'] == 2
    assert data['lessons_count'] == 3
    assert data['module_statuses'].count('available') == 1
    assert data['lesson_statuses'].count('available') == 1


def test_complete_first_lesson_unlocks_next_lesson():
    access = setup_user()

    # find first available lesson id via db-independent helper endpoint state assumptions
    # complete whichever first available is first in seeded order by querying internal table through flow
    # deterministic: first seeded lesson is first available
    from backend.app.database import SessionLocal
    from backend.app.course_entities import Lesson, UserLessonProgress
    from sqlalchemy import select

    db = SessionLocal()
    try:
        lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = lp.lesson_id
    finally:
        db.close()

    c = client.post(f'/api/progress/lessons/{lesson_id}/complete', cookies={'access_token': access})
    assert c.status_code == 200

    r = client.get('/api/progress', cookies={'access_token': access})
    assert r.status_code == 200
    data = r.json()
    assert data['lesson_statuses'].count('available') >= 1
    assert data['lesson_statuses'].count('completed') >= 1


def test_cannot_complete_locked_lesson():
    access = setup_user()
    from backend.app.database import SessionLocal
    from backend.app.course_entities import UserLessonProgress
    from sqlalchemy import select

    db = SessionLocal()
    try:
        locked = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'locked')).scalars().first()
        locked_id = locked.lesson_id
    finally:
        db.close()

    c = client.post(f'/api/progress/lessons/{locked_id}/complete', cookies={'access_token': access})
    assert c.status_code == 403
