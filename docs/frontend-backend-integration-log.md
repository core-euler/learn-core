# Frontend-Backend Integration Log

## Goal
Connect the current frontend (from `emergent_client`) with the real backend (from `main`) and track endpoint compatibility and merge progress.

## Scope
- Keep backend API as source of truth.
- Adapt frontend client/contracts to backend endpoints.
- Remove frontend assumptions that depend on mock-only API shapes.

## Baseline (2026-03-21)
- Branch context: backend from `main`, frontend synced from `emergent_client`.
- Initial frontend expected a different API contract in several places:
  - `auth/login` response shape
  - `modules/progress` data shape
  - chat payloads (`message_id`, exam `answers[]`)
  - consultant transport (frontend expected SSE, backend returns JSON)

## Compatibility Matrix
| Area | Endpoint(s) | Status | Notes |
|---|---|---|---|
| Auth | `POST /api/auth/login`, `GET /api/auth/me` | Fixed in frontend | Frontend now performs login then fetches `/auth/me` to resolve user profile. |
| Auth | `POST /api/auth/register` | Compatible | Frontend now sends backend-compatible payload (`email`, `password`). |
| Auth | `POST /api/auth/logout` | Compatible | CSRF interceptor preserved for state-changing requests. |
| Modules | `GET /api/modules`, `GET /api/modules/{id}` | Fixed in frontend | Added normalization layer to build UI module tree from backend responses. |
| Progress | `GET /api/progress`, `POST /api/progress/lessons/{id}/complete` | Fixed in frontend | Progress now used as source for module/lesson statuses and `next_lesson_id`. |
| Lesson content | `GET /api/lessons/{id}/content` | Compatible | Frontend now relies on real backend response only. |
| Lecture chat | `POST /api/chat/lecture` (JSON/SSE) | Fixed in frontend | Added required `message_id`; SSE parser aligned to backend `chunk/done` event format. |
| Exam chat | `POST /api/chat/exam/start`, `POST /api/chat/exam/finish` | Fixed in frontend | Frontend now sends `answers[]` instead of legacy `message`. |
| Consultant chat | `POST /api/chat/consultant` | Fixed in frontend | Switched from SSE expectation to backend JSON response flow. |
| CORS (local dev) | FastAPI CORS config | Fixed in backend | Default CORS now includes `localhost/127.0.0.1:3000` in addition to 5173. |

## Changes Applied
- Frontend API contract updates:
  - `frontend/src/utils/api.js`
  - `frontend/src/utils/sse.js`
  - `frontend/src/context/AuthContext.js`
  - `frontend/src/pages/MainPage.js`
  - `frontend/src/components/Sidebar.js`
  - `frontend/src/pages/LoginPage.js`
  - `frontend/src/pages/TelegramCallbackPage.js`
  - `frontend/src/App.js`
- Backend local-dev CORS update:
  - `backend/app/main.py`
- Telegram user profile support:
  - `backend/app/entities.py` (`last_name`)
  - `backend/app/schemas.py` (`last_name`, `full_name`)
  - `backend/app/main.py` (Telegram callback now accepts/signs `last_name`)
- Telegram bot:
  - `backend/bot/telegram_auth_bot.py`
  - `backend/requirements-bot.txt`
  - docs/env updates in README files

## Open Items
- Telegram auth requires a real bot setup (`TELEGRAM_BOT_TOKEN`, bot username, frontend URL envs).
- No dedicated frontend integration tests exist yet for this merged contract.
- Frontend dependency tree requires `--legacy-peer-deps` with current package set (`date-fns` v4 vs `react-day-picker` peer range).
- Docker policy now split env sources by service:
  - root `.env`: `db`, `backend`, `telegram-bot`
  - `frontend/.env.docker`: `frontend`

## Verification Plan
1. Backend API smoke (auth + modules + progress + chat) via pytest/TestClient.
2. Frontend runtime smoke with real backend URL (`REACT_APP_BACKEND_URL`).
3. Manual E2E path:
   - Login
   - Load next available lesson
   - Lecture request (SSE)
   - Exam start/finish
   - Consultant request after unlock

## Verification Log
- 2026-03-21: Contract alignment patches applied (frontend + CORS).
- 2026-03-21: Backend smoke tests passed (`30 passed`):
  - `backend/tests/test_auth_sessions.py`
  - `backend/tests/test_course_progress.py`
  - `backend/tests/test_ai_modes.py`
  - `backend/tests/test_frontend_api_compat.py`
- 2026-03-21: Frontend dependency install completed using `npm --prefix frontend install --legacy-peer-deps`.
- 2026-03-21: Frontend build passed cleanly (`npm --prefix frontend run build`).
- 2026-03-21: End-to-end API compatibility smoke passed (`INTEGRATION_SMOKE_OK`) against FastAPI `TestClient` using frontend-style payloads:
  - auth login + me
  - modules/progress/module details/lesson content
  - lecture SSE (`message_id` + `event: done`)
  - exam start + finish (`answers[]`)
  - consultant lock gate + unlock flow
- 2026-03-21: Telegram auth flow upgraded:
  - aiogram bot generates signed callback URL with `id`, `first_name`, `last_name`, `username`, `auth_date`, `hash`
  - frontend callback route consumes signed URL and finalizes backend session
  - backend persists and returns `first_name`/`last_name`/`full_name`
- 2026-03-21: `docker-compose` upgraded to full stack:
  - services: `db`, `backend`, `frontend`, `telegram-bot`
  - env source policy enforced (root `.env` for all except frontend)
- 2026-03-21: RAG runtime integrated with curriculum content:
  - startup ingestion from `backend/content/index.json` + markdown chunking
  - embeddings retrieval path via CometAPI (`COMETAPI_EMBED_MODEL=text-embedding-3-small`)
  - lexical fallback preserved when embeddings provider is unavailable
  - lecture/consultant prompts now include retrieved context blocks
- 2026-03-21: RAG indexing switched to incremental DB cache:
  - added `rag_chunks` + `rag_index_state` tables
  - startup computes `content_signature` from `index.json` + markdown files + chunk/embed settings
  - embeddings/chunk rebuild runs only when signature changes (or one-time embeddings backfill if previous build had no vectors)
- 2026-03-21: Backend regression gate after incremental RAG changes passed (`54 passed` for `backend/tests`).
- 2026-03-21: Course catalog switched to single source of truth:
  - backend startup now syncs `modules/lessons` from `backend/content/index.json` by stable slugs
  - existing users get missing progress rows auto-backfilled when catalog expands
- 2026-03-21: Backend regression gate after catalog sync changes passed (`56 passed` for `backend/tests`).
- 2026-03-21: Course index contract expanded:
  - documented canonical extended schema (`full_chapter`, `type`, `difficulty`, `prerequisites`, `tags`)
  - backend validator updated to enforce new metadata and prerequisite references
- 2026-03-21: Backend regression gate after course-format expansion passed (`57 passed` for `backend/tests`).
