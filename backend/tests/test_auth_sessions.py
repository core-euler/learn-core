import os
os.environ['APP_ENV'] = 'test'

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def reset_state():
    client.post('/_test/reset')


def register_user(email='user@example.com', password='password123'):
    return client.post('/api/auth/register', json={'email': email, 'password': password})


def login_user(email='user@example.com', password='password123'):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


def test_register_and_login_happy_path():
    reset_state()
    r = register_user()
    assert r.status_code == 201
    data = r.json()['user']
    assert data['email'] == 'user@example.com'

    l = login_user()
    assert l.status_code == 200
    assert 'access_token' in l.cookies
    assert 'refresh_token' in l.cookies


def test_login_invalid_credentials():
    reset_state()
    register_user()
    l = login_user(password='wrongpass')
    assert l.status_code == 401


def test_me_requires_access_cookie():
    reset_state()
    m = client.get('/api/auth/me')
    assert m.status_code == 401


def test_me_after_login():
    reset_state()
    register_user()
    l = login_user()
    cookies = l.cookies
    m = client.get('/api/auth/me', cookies=cookies)
    assert m.status_code == 200
    assert m.json()['email'] == 'user@example.com'


def test_refresh_rotation_and_old_token_invalid():
    reset_state()
    register_user()
    l = login_user()
    old_refresh = l.cookies.get('refresh_token')

    r1 = client.post('/api/auth/refresh', cookies={'refresh_token': old_refresh})
    assert r1.status_code == 200
    new_refresh = r1.cookies.get('refresh_token')
    assert new_refresh and new_refresh != old_refresh

    r2 = client.post('/api/auth/refresh', cookies={'refresh_token': old_refresh})
    assert r2.status_code == 401
    assert r2.json()['detail'] == 'refresh_reuse_detected'

    # After reuse detection, even the latest refresh must be revoked.
    r3 = client.post('/api/auth/refresh', cookies={'refresh_token': new_refresh})
    assert r3.status_code == 401


def test_logout_revokes_current_session():
    reset_state()
    register_user()
    l = login_user()
    refresh = l.cookies.get('refresh_token')

    lo = client.post('/api/auth/logout', cookies={'refresh_token': refresh})
    assert lo.status_code == 200

    r = client.post('/api/auth/refresh', cookies={'refresh_token': refresh})
    assert r.status_code == 401


def test_logout_all_revokes_all_sessions_for_user():
    reset_state()
    register_user()

    s1 = login_user()
    s2 = login_user()

    access = s1.cookies.get('access_token')
    r1 = s1.cookies.get('refresh_token')
    r2 = s2.cookies.get('refresh_token')

    out = client.post('/api/auth/logout-all', cookies={'access_token': access})
    assert out.status_code == 200

    x1 = client.post('/api/auth/refresh', cookies={'refresh_token': r1})
    x2 = client.post('/api/auth/refresh', cookies={'refresh_token': r2})
    assert x1.status_code == 401
    assert x2.status_code == 401
