import os

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_test_routes_available_in_test_env(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'test')
    r1 = client.post('/_test/reset')
    r2 = client.post('/_test/seed-course')
    assert r1.status_code == 200
    assert r2.status_code == 200


def test_test_routes_blocked_in_prod_like_env(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'prod')

    reset = client.post('/_test/reset')
    seed = client.post('/_test/seed-course')
    minute = client.post('/_test/reset-minute-window')

    assert reset.status_code == 404
    assert seed.status_code == 404
    assert minute.status_code == 404
