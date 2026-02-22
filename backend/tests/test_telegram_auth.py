import os
import time
import hashlib
import hmac
from urllib.parse import urlencode

os.environ['APP_ENV'] = 'test'
os.environ['TELEGRAM_BOT_TOKEN'] = 'test-bot-token'

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings


client = TestClient(app)


def sign_payload(payload: dict, bot_token: str) -> str:
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def test_telegram_callback_happy_path():
    settings.telegram_bot_token = 'test-bot-token'
    client.post('/_test/reset')
    payload = {
        'id': '123456',
        'first_name': 'Kolya',
        'username': 'okoloboga',
        'photo_url': 'https://example.com/a.jpg',
        'auth_date': str(int(time.time())),
    }
    payload['hash'] = sign_payload(payload, 'test-bot-token')

    r = client.get('/api/auth/telegram/callback', params=payload)
    assert r.status_code == 200
    assert 'access_token' in r.cookies
    assert 'refresh_token' in r.cookies


def test_telegram_callback_invalid_hash_rejected():
    settings.telegram_bot_token = 'test-bot-token'
    client.post('/_test/reset')
    payload = {
        'id': '123456',
        'first_name': 'Kolya',
        'username': 'okoloboga',
        'photo_url': 'https://example.com/a.jpg',
        'auth_date': str(int(time.time())),
        'hash': 'badhash',
    }
    r = client.get('/api/auth/telegram/callback', params=payload)
    assert r.status_code == 401


def test_telegram_callback_stale_auth_rejected():
    settings.telegram_bot_token = 'test-bot-token'
    client.post('/_test/reset')
    payload = {
        'id': '123456',
        'first_name': 'Kolya',
        'username': 'okoloboga',
        'photo_url': 'https://example.com/a.jpg',
        'auth_date': str(int(time.time()) - 90000),
    }
    payload['hash'] = sign_payload(payload, 'test-bot-token')

    r = client.get('/api/auth/telegram/callback', params=payload)
    assert r.status_code == 401
