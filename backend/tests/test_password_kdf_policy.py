import os
os.environ['APP_ENV'] = 'test'

import hashlib

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.main import app
from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.entities import User


client = TestClient(app)


def reset_state():
    client.post('/_test/reset')


def register_user(email='user@example.com', password='password123'):
    return client.post('/api/auth/register', json={'email': email, 'password': password})


def login_user(email='user@example.com', password='password123'):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


def _legacy_hash(password: str) -> str:
    salt = 'legacysalt'
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f'{salt}${digest}'


def test_register_uses_configured_scrypt_policy_by_default():
    reset_state()
    settings.password_kdf_algorithm = 'scrypt'

    r = register_user()
    assert r.status_code == 201

    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == 'user@example.com')).scalar_one()
        assert user.password_hash.startswith('scrypt$')


def test_login_migrates_legacy_hash_to_current_policy():
    reset_state()
    settings.password_kdf_algorithm = 'scrypt'
    settings.password_migrate_on_login = True
    settings.password_legacy_accept = True

    register_user()
    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == 'user@example.com')).scalar_one()
        user.password_hash = _legacy_hash('password123')
        db.commit()

    login = login_user()
    assert login.status_code == 200

    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == 'user@example.com')).scalar_one()
        assert user.password_hash.startswith('scrypt$')
        assert '$' in user.password_hash


def test_register_and_login_with_argon2id_policy():
    reset_state()
    settings.password_kdf_algorithm = 'argon2id'

    r = register_user(email='argon@example.com', password='strong-pass-123')
    assert r.status_code == 201

    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == 'argon@example.com')).scalar_one()
        assert user.password_hash.startswith('argon2id$')

    l = login_user(email='argon@example.com', password='strong-pass-123')
    assert l.status_code == 200
