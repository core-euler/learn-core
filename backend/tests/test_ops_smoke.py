import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "test"

from backend.app.main import app  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]


def _parse_env_example_keys() -> set[str]:
    env_path = REPO_ROOT / ".env.example"
    assert env_path.exists(), ".env.example is missing"

    keys: set[str] = set()
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key:
            keys.add(key)
    return keys


def test_healthz_endpoint_returns_ok() -> None:
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_env_example_contains_required_runtime_keys() -> None:
    keys = _parse_env_example_keys()
    required = {
        "APP_ENV",
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "JWT_ALGORITHM",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "COOKIE_SECURE",
        "COOKIE_SAMESITE",
        "CONTENT_VALIDATE_ON_STARTUP",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    }
    assert required.issubset(keys)
