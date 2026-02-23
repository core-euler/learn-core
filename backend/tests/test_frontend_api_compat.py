import os

os.environ['APP_ENV'] = 'test'

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.course_entities import UserLessonProgress
from backend.app.main import app


client = TestClient(app)


def csrf_headers(cookies):
    token = cookies.get('csrf_token') if cookies else None
    return {'x-csrf-token': token} if token else {}


def setup_user():
    client.post('/_test/reset')
    client.post('/_test/seed-course')
    client.post('/api/auth/register', json={'email': 'frontend@example.com', 'password': 'password123'})
    login = client.post('/api/auth/login', json={'email': 'frontend@example.com', 'password': 'password123'})
    return login.cookies


def _available_lesson_id():
    db = SessionLocal()
    try:
        return db.execute(select(UserLessonProgress).where(UserLessonProgress.status == 'available')).scalar_one().lesson_id
    finally:
        db.close()


def test_progress_and_modules_shapes_for_frontend_dashboard():
    cookies = setup_user()

    progress = client.get('/api/progress', cookies={'access_token': cookies.get('access_token')})
    assert progress.status_code == 200
    body = progress.json()
    assert isinstance(body['overall_percent'], int)
    assert 'next_lesson_id' in body
    assert isinstance(body['consultant_unlocked'], bool)
    assert isinstance(body['modules'], list)
    assert body['modules']
    assert body['next_lesson_id'] is not None
    assert body['consultant_unlocked'] is False

    first_module = body['modules'][0]
    assert {'module_id', 'status', 'completed_at', 'lessons'} <= set(first_module.keys())

    first_lesson = first_module['lessons'][0]
    assert {'lesson_id', 'status', 'exam_score', 'exam_attempts', 'completed_at'} <= set(first_lesson.keys())

    modules = client.get('/api/modules')
    assert modules.status_code == 200
    mods = modules.json()['modules']
    assert mods
    assert {'id', 'title', 'description', 'order_index', 'lessons_count'} <= set(mods[0].keys())


def test_chat_response_shapes_and_limits_error_codes_for_frontend():
    cookies = setup_user()
    lesson_id = _available_lesson_id()

    lecture = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'hello',
        'message_id': 'fe-lecture-1',
    })
    assert lecture.status_code == 200
    lecture_body = lecture.json()
    assert {'session_id', 'reply', 'provider', 'fallback_used', 'fallback_reason', 'retrieval'} <= set(lecture_body.keys())
    assert {'top_k', 'chunks_found', 'citations'} <= set(lecture_body['retrieval'].keys())

    consultant_denied = client.post('/api/chat/consultant', cookies=cookies, headers=csrf_headers(cookies), json={
        'session_id': None,
        'message': 'help',
        'message_id': 'fe-consultant-0',
    })
    assert consultant_denied.status_code == 403

    client.post('/_test/reset-minute-window', cookies={'access_token': cookies.get('access_token')})

    # Burn minute bucket to verify stable error code consumed by frontend mapping.
    for i in range(20):
        r = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
            'lesson_id': lesson_id,
            'session_id': None,
            'message': f'minute {i}',
            'message_id': f'fe-minute-{i}',
        })
        assert r.status_code == 200

    blocked = client.post('/api/chat/lecture', cookies=cookies, headers=csrf_headers(cookies), json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'blocked',
        'message_id': 'fe-minute-over',
    })
    assert blocked.status_code == 429
    assert blocked.json()['detail'] in {'minute_rate_limited', 'daily_limit_exceeded'}


def test_progress_exposes_consultant_gate_after_module_completion():
    cookies = setup_user()

    first = _available_lesson_id()
    client.post(f'/api/progress/lessons/{first}/complete', cookies=cookies, headers=csrf_headers(cookies))
    second = _available_lesson_id()
    client.post(f'/api/progress/lessons/{second}/complete', cookies=cookies, headers=csrf_headers(cookies))

    progress = client.get('/api/progress', cookies={'access_token': cookies.get('access_token')})
    assert progress.status_code == 200
    assert progress.json()['consultant_unlocked'] is True


def test_consultant_is_json_response_not_sse():
    cookies = setup_user()

    # unlock consultant gate: complete two lessons in first module
    first = _available_lesson_id()
    client.post(f'/api/progress/lessons/{first}/complete', cookies=cookies, headers=csrf_headers(cookies))
    second = _available_lesson_id()
    client.post(f'/api/progress/lessons/{second}/complete', cookies=cookies, headers=csrf_headers(cookies))

    response = client.post('/api/chat/consultant', cookies=cookies, headers={**csrf_headers(cookies), 'accept': 'text/event-stream'}, json={
        'session_id': None,
        'message': 'consult me',
        'message_id': 'fe-consultant-1',
    })
    assert response.status_code == 200
    assert 'text/event-stream' not in response.headers.get('content-type', '')
    body = response.json()
    assert {'session_id', 'reply', 'source', 'provider', 'fallback_used', 'fallback_reason', 'retrieval'} <= set(body.keys())
