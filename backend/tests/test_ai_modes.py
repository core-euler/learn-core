import os
import time
os.environ['APP_ENV'] = 'test'

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.course_entities import UserLessonProgress


client = TestClient(app)


def csrf_headers(cookies):
    token = cookies.get('csrf_token') if cookies else None
    return {'x-csrf-token': token} if token else {}


def setup_user():
    client.post('/_test/reset')
    client.post('/_test/seed-course')
    client.post('/api/auth/register', json={'email': 'ai@example.com', 'password': 'password123'})
    l = client.post('/api/auth/login', json={'email': 'ai@example.com', 'password': 'password123'})
    return l.cookies


def test_lecture_mode_requires_available_lesson():
    cookies = setup_user()
    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        locked = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'locked')).scalars().first()
        available_id, locked_id = available.lesson_id, locked.lesson_id
    finally:
        db.close()

    ok = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
        'lesson_id': available_id,
        'session_id': None,
        'message': 'hello',
        'message_id': 'm1'
    })
    assert ok.status_code == 200
    assert 'session_id' in ok.json()
    assert ok.json()['fallback_used'] is False
    assert ok.json()['fallback_reason'] == 'ok'

    denied = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
        'lesson_id': locked_id,
        'session_id': None,
        'message': 'hello',
        'message_id': 'm2'
    })
    assert denied.status_code == 403


def test_exam_start_finish_sessions_and_consultant_gate():
    cookies = setup_user()

    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        available_id = available.lesson_id
    finally:
        db.close()

    ex = client.post('/api/chat/exam/start', cookies=cookies, headers=csrf_headers(cookies), json={'lesson_id': available_id})
    assert ex.status_code == 200
    assert len(ex.json()['questions']) == 5
    sid = ex.json()['session_id']

    finish = client.post('/api/chat/exam/finish', cookies=cookies, headers=csrf_headers(cookies), json={
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

    sessions = client.get('/api/chat/sessions', cookies={'access_token': cookies.get('access_token')})
    assert sessions.status_code == 200
    assert len(sessions.json()['sessions']) >= 1

    one = client.get(f"/api/chat/sessions/{sid}", cookies={'access_token': cookies.get('access_token')})
    assert one.status_code == 200

    consultant_denied = client.post('/api/chat/consultant', cookies=cookies, headers=csrf_headers(cookies), json={
        'session_id': None,
        'message': 'help',
        'message_id': 'c1'
    })
    assert consultant_denied.status_code == 403

    client.post(f'/api/progress/lessons/{available_id}/complete', cookies=cookies, headers=csrf_headers(cookies))
    db = SessionLocal()
    try:
        next_available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalars().first()
        next_id = next_available.lesson_id
    finally:
        db.close()

    client.post(f'/api/progress/lessons/{next_id}/complete', cookies=cookies, headers=csrf_headers(cookies))

    consultant_ok = client.post('/api/chat/consultant', cookies=cookies, headers=csrf_headers(cookies), json={
        'session_id': None,
        'message': 'help',
        'message_id': 'c2'
    })
    assert consultant_ok.status_code == 200
    assert consultant_ok.json()['fallback_used'] is False


def test_lecture_sse_stream_contract():
    cookies = setup_user()

    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = available.lesson_id
    finally:
        db.close()

    r = client.post('/api/chat/lecture', cookies=cookies, headers={'accept': 'text/event-stream', **csrf_headers(cookies)}, json={
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

    r2 = client.post('/api/chat/lecture', cookies=cookies, headers={'accept': 'text/event-stream', 'last-event-id': 'stream-1', **csrf_headers(cookies)}, json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'hello stream',
        'message_id': 'stream-1'
    })
    assert r2.status_code == 200
    body2 = r2.text
    assert '"type": "chunk"' not in body2
    assert '"type": "done"' in body2


def test_daily_limit_enforced_on_chat_requests():
    cookies = setup_user()

    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = available.lesson_id
    finally:
        db.close()

    for i in range(20):
        r = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
            'lesson_id': lesson_id,
            'session_id': None,
            'message': f'hello {i}',
            'message_id': f'm{i}'
        })
        assert r.status_code == 200

    client.post('/_test/reset-minute-window', cookies={'access_token': cookies.get('access_token')})

    for i in range(20, 30):
        r = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
            'lesson_id': lesson_id,
            'session_id': None,
            'message': f'hello {i}',
            'message_id': f'm{i}'
        })
        assert r.status_code == 200

    blocked = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'overflow',
        'message_id': 'm-over'
    })
    assert blocked.status_code == 429
    assert blocked.json()['detail'] == 'daily_limit_exceeded'


def test_minute_limit_enforced_before_daily_limit():
    cookies = setup_user()

    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = available.lesson_id
    finally:
        db.close()

    for i in range(20):
        r = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
            'lesson_id': lesson_id,
            'session_id': None,
            'message': f'minute {i}',
            'message_id': f'min-{i}'
        })
        assert r.status_code == 200

    blocked = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'minute over',
        'message_id': 'min-over'
    })
    assert blocked.status_code == 429
    assert blocked.json()['detail'] == 'minute_rate_limited'


def test_chat_endpoints_reject_missing_or_invalid_csrf():
    cookies = setup_user()
    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one()
        lesson_id = available.lesson_id
    finally:
        db.close()

    missing = client.post('/api/chat/lecture', cookies=cookies, json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'no csrf',
        'message_id': 'csrf-0'
    })
    assert missing.status_code == 403
    assert missing.json()['detail'] == 'csrf_failed'

    invalid = client.post('/api/chat/exam/start', cookies=cookies, headers={'x-csrf-token': 'bad'}, json={'lesson_id': lesson_id})
    assert invalid.status_code == 403
    assert invalid.json()['detail'] == 'csrf_failed'


def test_lecture_timeout_uses_fallback(monkeypatch):
    cookies = setup_user()
    db = SessionLocal()
    try:
        lesson_id = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one().lesson_id
    finally:
        db.close()

    old_timeout = app.state.llm_policy.timeout_seconds

    class SlowAdapter:
        def lecture_reply(self, *, lesson_id: str, message: str, message_id: str):
            time.sleep(0.15)
            return type('R', (), {'text': 'late', 'tokens_used': 1, 'provider': 'slow'})()

        def consultant_reply(self, *, message: str, message_id: str):
            return type('R', (), {'text': 'ok', 'tokens_used': 1, 'provider': 'slow'})()

        def build_exam(self, *, lesson_id: str):
            return {'questions': [], 'provider': 'slow'}

    monkeypatch.setattr(app.state, 'llm_adapter', SlowAdapter())
    app.state.llm_policy.timeout_seconds = 0.05

    try:
        r = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
            'lesson_id': lesson_id,
            'session_id': None,
            'message': 'hello',
            'message_id': 'timeout-1'
        })
    finally:
        app.state.llm_policy.timeout_seconds = old_timeout

    assert r.status_code == 200
    assert r.json()['fallback_used'] is True
    assert r.json()['fallback_reason'] == 'timeout'
    assert r.json()['provider'] == 'fallback'


def test_consultant_error_uses_fallback(monkeypatch):
    cookies = setup_user()

    class ErrorAdapter:
        def lecture_reply(self, *, lesson_id: str, message: str, message_id: str):
            return type('R', (), {'text': 'ok', 'tokens_used': 1, 'provider': 'err'})()

        def consultant_reply(self, *, message: str, message_id: str):
            raise RuntimeError('boom')

        def build_exam(self, *, lesson_id: str):
            return {'questions': [], 'provider': 'err'}

    monkeypatch.setattr(app.state, 'llm_adapter', ErrorAdapter())

    # unlock consultant gate quickly
    db = SessionLocal()
    try:
        available = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one().lesson_id
    finally:
        db.close()
    client.post(f'/api/progress/lessons/{available}/complete', cookies=cookies, headers=csrf_headers(cookies))
    db = SessionLocal()
    try:
        next_id = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalars().first().lesson_id
    finally:
        db.close()
    client.post(f'/api/progress/lessons/{next_id}/complete', cookies=cookies, headers=csrf_headers(cookies))

    r = client.post('/api/chat/consultant', cookies=cookies, headers=csrf_headers(cookies), json={
        'session_id': None,
        'message': 'help',
        'message_id': 'err-1'
    })
    assert r.status_code == 200
    assert r.json()['fallback_used'] is True
    assert r.json()['fallback_reason'] == 'error'
    assert r.json()['provider'] == 'fallback'


def test_exam_start_falls_back_to_default_adapter_on_provider_error(monkeypatch):
    cookies = setup_user()
    db = SessionLocal()
    try:
        lesson_id = db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one().lesson_id
    finally:
        db.close()

    class ErrorExamAdapter:
        def lecture_reply(self, *, lesson_id: str, message: str, message_id: str):
            return type('R', (), {'text': 'ok', 'tokens_used': 1, 'provider': 'x'})()

        def consultant_reply(self, *, message: str, message_id: str):
            return type('R', (), {'text': 'ok', 'tokens_used': 1, 'provider': 'x'})()

        def build_exam(self, *, lesson_id: str):
            raise RuntimeError('exam failed')

    monkeypatch.setattr(app.state, 'llm_adapter', ErrorExamAdapter())

    r = client.post('/api/chat/exam/start', cookies=cookies, headers=csrf_headers(cookies), json={'lesson_id': lesson_id})
    assert r.status_code == 200
    assert r.json()['provider'] == 'fallback'
    assert r.json()['fallback_reason'] == 'error'
    assert len(r.json()['questions']) == 5
