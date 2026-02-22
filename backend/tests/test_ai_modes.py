from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.course_entities import UserLessonProgress


client = TestClient(app)


def setup_user():
    client.post('/_test/reset')
    client.post('/_test/seed-course')
    client.post('/api/auth/register', json={'email': 'ai@example.com', 'password': 'password123'})
    l = client.post('/api/auth/login', json={'email': 'ai@example.com', 'password': 'password123'})
    return l.cookies.get('access_token')


def test_lecture_mode_requires_available_lesson():
    access = setup_user()
    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        locked = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'locked')).scalars().first()
        available_id, locked_id = available.lesson_id, locked.lesson_id
    finally:
        db.close()

    ok = client.post('/api/chat/lecture', cookies={'access_token': access}, json={
        'lesson_id': available_id,
        'session_id': None,
        'message': 'hello',
        'message_id': 'm1'
    })
    assert ok.status_code == 200
    assert 'session_id' in ok.json()

    denied = client.post('/api/chat/lecture', cookies={'access_token': access}, json={
        'lesson_id': locked_id,
        'session_id': None,
        'message': 'hello',
        'message_id': 'm2'
    })
    assert denied.status_code == 403


def test_exam_start_finish_sessions_and_consultant_gate():
    access = setup_user()

    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        available_id = available.lesson_id
    finally:
        db.close()

    ex = client.post('/api/chat/exam/start', cookies={'access_token': access}, json={'lesson_id': available_id})
    assert ex.status_code == 200
    assert len(ex.json()['questions']) == 5
    sid = ex.json()['session_id']

    finish = client.post('/api/chat/exam/finish', cookies={'access_token': access}, json={
        'session_id': sid,
        'answers': [
            {'question_id': 1, 'answer': 'A'},
            {'question_id': 2, 'answer': 'B'},
            {'question_id': 3, 'answer': 'C'},
            {'question_id': 4, 'answer': 'x'},
            {'question_id': 5, 'answer': 'x'},
        ]
    })
    assert finish.status_code == 200
    assert finish.json()['passed'] is True

    sessions = client.get('/api/chat/sessions', cookies={'access_token': access})
    assert sessions.status_code == 200
    assert len(sessions.json()['sessions']) >= 1

    one = client.get(f"/api/chat/sessions/{sid}", cookies={'access_token': access})
    assert one.status_code == 200

    consultant_denied = client.post('/api/chat/consultant', cookies={'access_token': access}, json={
        'session_id': None,
        'message': 'help',
        'message_id': 'c1'
    })
    assert consultant_denied.status_code == 403

    # complete full module and try again
    client.post(f'/api/progress/lessons/{available_id}/complete', cookies={'access_token': access})
    db = SessionLocal()
    try:
        next_available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalars().first()
        next_id = next_available.lesson_id
    finally:
        db.close()

    client.post(f'/api/progress/lessons/{next_id}/complete', cookies={'access_token': access})

    consultant_ok = client.post('/api/chat/consultant', cookies={'access_token': access}, json={
        'session_id': None,
        'message': 'help',
        'message_id': 'c2'
    })
    assert consultant_ok.status_code == 200


def test_lecture_sse_stream_contract():
    access = setup_user()

    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = available.lesson_id
    finally:
        db.close()

    r = client.post('/api/chat/lecture', cookies={'access_token': access}, headers={'accept': 'text/event-stream'}, json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'hello stream',
        'message_id': 'stream-1'
    })
    assert r.status_code == 200
    assert 'text/event-stream' in r.headers.get('content-type', '')
    body = r.text
    assert '"type": "chunk"' in body
    assert '"type": "done"' in body


def test_daily_limit_enforced_on_chat_requests():
    access = setup_user()

    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = available.lesson_id
    finally:
        db.close()

    for i in range(30):
        r = client.post('/api/chat/lecture', cookies={'access_token': access}, json={
            'lesson_id': lesson_id,
            'session_id': None,
            'message': f'hello {i}',
            'message_id': f'm{i}'
        })
        assert r.status_code == 200

    blocked = client.post('/api/chat/lecture', cookies={'access_token': access}, json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'overflow',
        'message_id': 'm-over'
    })
    assert blocked.status_code == 429
