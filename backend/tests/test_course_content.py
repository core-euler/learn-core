from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.course_entities import Lesson, UserLessonProgress


client = TestClient(app)


def setup_user():
    client.post('/_test/reset')
    client.post('/_test/seed-course')
    client.post('/api/auth/register', json={'email': 'c@example.com', 'password': 'password123'})
    l = client.post('/api/auth/login', json={'email': 'c@example.com', 'password': 'password123'})
    return l.cookies.get('access_token')


def test_get_modules_and_module_details():
    access = setup_user()
    r = client.get('/api/modules')
    assert r.status_code == 200
    assert len(r.json()['modules']) == 2

    mod_id = r.json()['modules'][0]['id']
    d = client.get(f'/api/modules/{mod_id}')
    assert d.status_code == 200
    assert len(d.json()['lessons']) >= 1


def test_get_lesson_and_content_access_rules():
    access = setup_user()

    db = SessionLocal()
    try:
        available_lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        locked_lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'locked')).scalars().first()
        available_lesson_id = available_lp.lesson_id
        locked_lesson_id = locked_lp.lesson_id
    finally:
        db.close()

    l = client.get(f'/api/lessons/{available_lesson_id}')
    assert l.status_code == 200

    c1 = client.get(f'/api/lessons/{available_lesson_id}/content', cookies={'access_token': access})
    assert c1.status_code == 200
    assert 'content' in c1.json()

    c2 = client.get(f'/api/lessons/{locked_lesson_id}/content', cookies={'access_token': access})
    assert c2.status_code == 403
    assert c2.json()['detail'] == 'lesson_locked'
