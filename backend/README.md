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
- Расширен AI API: exam finish, sessions history.
- Начат phase-5: базовые usage лимиты для chat endpoint-ов.
- Добавлен базовый SSE ответ для lecture режима (event-stream).
- Добавлены дневной + минутный лимиты для chat endpoint-ов.
- Добавлена базовая reconnect-дедуп логика по `Last-Event-ID`.

## Запуск тестов
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```
