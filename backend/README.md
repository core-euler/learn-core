# Backend (MVP implementation)

Текущий статус: backend MVP-ядро реализовано, идёт hardening + productionization.

Реализовано на текущий момент:
- FastAPI приложение с auth endpoints:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `POST /api/auth/refresh`
  - `POST /api/auth/logout`
  - `POST /api/auth/logout-all`
  - `GET /api/auth/me`
- SQLAlchemy persistence слой для пользователей и сессий.
- Alembic migrations (`alembic upgrade head`, initial migration создан).
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
- Test-only endpoints теперь доступны только при `APP_ENV=test`.
- Cookie flags (`secure`, `samesite`) управляются env-переменными.
- LLM provider switch через env:
  - `LLM_PROVIDER=default|cometapi`
  - при `cometapi` используются `COMETAPI_API_KEY`, `COMETAPI_BASE_URL`, `COMETAPI_CHAT_MODEL`, `COMETAPI_EXAM_MODEL`, `COMETAPI_EMBED_MODEL`.
- RAG ingestion/retrieval:
  - индексация учебного контента из `backend/content/index.json` выполняется на старте приложения;
  - при доступном embeddings provider используется векторный поиск, иначе lexical fallback;
  - индексация инкрементальная: пересчёт запускается только при изменении `index.json`/markdown или параметров chunk/embed модели; иначе используется кэш в БД (`rag_chunks`, `rag_index_state`).
- Course catalog sync:
  - `backend/content/index.json` используется как source of truth для `modules/lessons`;
  - на старте backend выполняется upsert-синхронизация курса в БД по `slug`;
  - при изменениях курса для существующих пользователей автоматически добавляются отсутствующие записи прогресса.
  - поддерживается расширенный lesson metadata формат: `type`, `difficulty`, `prerequisites`, `tags` + `full_chapter` на уровне модуля.

## Запуск тестов
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Миграции
```bash
# по умолчанию sqlite:///./backend_dev.db
alembic upgrade head
alembic downgrade base
alembic current
```

## Telegram auth bot (aiogram)
В проект добавлен простой бот для Telegram login flow:
- файл: `backend/bot/telegram_auth_bot.py`
- зависимость: `backend/requirements-bot.txt`

Запуск:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-bot.txt

export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_AUTH_FRONTEND_URL=http://localhost:3000

python backend/bot/telegram_auth_bot.py
```

Бот отправляет пользователю подписанную ссылку вида:
`/auth/telegram/callback?id=...&first_name=...&last_name=...&...&hash=...`
Эта ссылка обрабатывается frontend callback-страницей, а затем передаётся в backend `/api/auth/telegram/callback`.

При запуске через `docker compose` бот поднимается отдельным сервисом `telegram-bot` и читает env из корневого `.env`.
