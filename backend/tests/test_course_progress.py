import os
os.environ['APP_ENV'] = 'test'

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def csrf_headers(cookies):
    token = cookies.get('csrf_token') if cookies else None
    return {'x-csrf-token': token} if token else {}


def setup_user():
    client.post('/_test/reset')
    client.post('/_test/seed-course')
    client.post('/api/auth/register', json={'email': 'p@example.com', 'password': 'password123'})
    l = client.post('/api/auth/login', json={'email': 'p@example.com', 'password': 'password123'})
    return l.cookies


def test_bootstrap_progress_initial_unlocks():
    cookies = setup_user()
    r = client.get('/api/progress', cookies={'access_token': cookies.get('access_token')})
    assert r.status_code == 200
    data = r.json()
    assert 'overall_percent' in data
    assert len(data['modules']) == 2
    all_lessons = [ls for m in data['modules'] for ls in m['lessons']]
    assert sum(1 for m in data['modules'] if m['status'] == 'available') == 1
    assert sum(1 for l in all_lessons if l['status'] == 'available') == 1


def test_complete_first_lesson_unlocks_next_lesson():
    cookies = setup_user()

    from backend.app.database import SessionLocal
    from backend.app.course_entities import UserLessonProgress
    from sqlalchemy import select

    db = SessionLocal()
    try:
        lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = lp.lesson_id
    finally:
        db.close()

    c = client.post(f'/api/progress/lessons/{lesson_id}/complete', cookies=cookies, headers=csrf_headers(cookies))
    assert c.status_code == 200

    r = client.get('/api/progress', cookies={'access_token': cookies.get('access_token')})
    assert r.status_code == 200
    data = r.json()
    all_lessons = [ls for m in data['modules'] for ls in m['lessons']]
    assert sum(1 for l in all_lessons if l['status'] == 'available') >= 1
    assert sum(1 for l in all_lessons if l['status'] == 'completed') >= 1


def test_cannot_complete_locked_lesson():
    cookies = setup_user()
    from backend.app.database import SessionLocal
    from backend.app.course_entities import UserLessonProgress
    from sqlalchemy import select

    db = SessionLocal()
    try:
        locked = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'locked')).scalars().first()
        locked_id = locked.lesson_id
    finally:
        db.close()

    c = client.post(f'/api/progress/lessons/{locked_id}/complete', cookies=cookies, headers=csrf_headers(cookies))
    assert c.status_code == 403


def test_progress_stats_shape():
    cookies = setup_user()
    s = client.get('/api/progress/stats', cookies={'access_token': cookies.get('access_token')})
    assert s.status_code == 200
    data = s.json()
    assert data['total_lessons'] == 3
    assert data['total_modules'] == 2
    assert 'requests_limit_today' in data


def test_complete_requires_csrf():
    cookies = setup_user()
    from backend.app.database import SessionLocal
    from backend.app.course_entities import UserLessonProgress
    from sqlalchemy import select

    db = SessionLocal()
    try:
        lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = lp.lesson_id
    finally:
        db.close()

    missing = client.post(f'/api/progress/lessons/{lesson_id}/complete', cookies=cookies)
    assert missing.status_code == 403
    assert missing.json()['detail'] == 'csrf_failed'
