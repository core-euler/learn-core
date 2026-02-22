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
- SQLAlchemy persistence слой для пользователей и сессий.
- Docker Compose окружение с PostgreSQL (`docker-compose.yml`).
- Покрытие тестами phase-2 auth/session контрактов (`backend/tests/test_auth_sessions.py`).
- Начат phase-3: course/progress сущности и тесты (`backend/tests/test_course_progress.py`).
- Добавлены phase-3 content endpoints и тесты (`backend/tests/test_course_content.py`).
- Начат phase-4 AI scaffold и тесты режимов (`backend/tests/test_ai_modes.py`).

## Запуск тестов
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```
