import os
os.environ['APP_ENV'] = 'test'

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def csrf_headers(cookies):
    token = cookies.get('csrf_token') if cookies else None
    return {'x-csrf-token': token} if token else {}


def test_smoke_e2e_happy_path_auth_course_progress_ai():
    # deterministic test fixtures for speed and stability
    client.post('/_test/reset')
    client.post('/_test/seed-course')

    register = client.post('/api/auth/register', json={'email': 'smoke@example.com', 'password': 'password123'})
    assert register.status_code == 201

    login = client.post('/api/auth/login', json={'email': 'smoke@example.com', 'password': 'password123'})
    assert login.status_code == 200
    assert login.cookies.get('access_token')
    assert login.cookies.get('refresh_token')
    assert login.cookies.get('csrf_token')

    me = client.get('/api/auth/me', cookies=login.cookies)
    assert me.status_code == 200
    assert me.json()['email'] == 'smoke@example.com'

    modules = client.get('/api/modules')
    assert modules.status_code == 200
    assert len(modules.json()['modules']) >= 1

    progress_before = client.get('/api/progress', cookies=login.cookies)
    assert progress_before.status_code == 200
    body_before = progress_before.json()
    assert body_before['overall_percent'] == 0
    lesson_id = body_before['next_lesson_id']
    assert lesson_id

    lesson_content = client.get(f'/api/lessons/{lesson_id}/content', cookies=login.cookies)
    assert lesson_content.status_code == 200
    assert lesson_content.json()['lesson_id'] == lesson_id

    lecture = client.post('/api/chat/lecture', cookies=login.cookies, headers=csrf_headers(login.cookies), json={
        'lesson_id': lesson_id,
        'session_id': None,
        'message': 'smoke happy path',
        'message_id': 'smoke-happy-1',
    })
    assert lecture.status_code == 200
    lecture_json = lecture.json()
    assert lecture_json['session_id']
    assert lecture_json['fallback_reason'] == 'ok'
    assert lecture_json['fallback_used'] is False

    complete = client.post(f'/api/progress/lessons/{lesson_id}/complete', cookies=login.cookies, headers=csrf_headers(login.cookies))
    assert complete.status_code == 200

    progress_after = client.get('/api/progress', cookies=login.cookies)
    assert progress_after.status_code == 200
    body_after = progress_after.json()
    assert body_after['overall_percent'] > body_before['overall_percent']
