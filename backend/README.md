# Backend (MVP bootstrap)

Текущий статус: старт реализации backend.

Реализовано в первом инкременте:
- FastAPI приложение с auth endpoints:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `POST /api/auth/refresh`
  - `POST /api/auth/logout`
  - `POST /api/auth/logout-all`
  - `GET /api/auth/me`
- In-memory хранилище для пользователей и сессий (временный слой для TDD-цикла).
- Покрытие тестами phase-2 auth/session контрактов (`backend/tests/test_auth_sessions.py`).

## Запуск тестов
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```
