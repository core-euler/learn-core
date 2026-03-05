# Release Readiness (Closed Testing)

_Last sync: 2026-03-05 (documentation consistency pass)_

## Current Backend Status Snapshot
- Auth/session core: implemented
- Course/progress core: implemented
- AI provider adapter: implemented (lecture/consultant/exam wired через adapter + fallback policy)
- Minimal RAG retrieval contract: implemented (retriever interface + stub index + lecture/consultant retrieval envelope with citations)
- Streaming: SSE for lecture с reconnect/replay protocol (`id=<message_id>:<seq>`, partial resume, duplicate prevention)
- Limits: daily + minute rate limits implemented
- Frontend API compatibility baseline: aligned (response-shape pass 4.1, including lecture SSE vs consultant JSON distinction)
- Minimal app shell readiness (4.2): confirmed, включая server-computed shell helpers в `/api/progress` (`next_lesson_id`, `consultant_unlocked`)

## Security/Hardening Checklist
- [x] httpOnly auth cookies
- [x] Configurable cookie flags (`secure`, `samesite`) via env
- [x] Test-only endpoints restricted to `APP_ENV=test` (+ smoke in prod-like env)
- [x] CSRF protection (double-submit) for state-changing endpoints
- [x] Telegram OAuth cryptographic validation: HMAC + freshness + bot-id binding
- [x] Password hashing policy upgrade for production KDF (`scrypt`/`argon2id`, env-configurable, login-time migration)

## Data/Infra Checklist
- [x] Docker compose with PostgreSQL + backend
- [x] Healthchecks wired for `db` and `backend` (`/healthz`)
- [x] `.env.example` with required runtime/ops keys and safe local defaults
- [x] Local + staging runbook documented (`docs/runbook.md`)
- [x] SQLAlchemy persistence in place
- [x] Alembic migrations introduced (initial revision + runbook + smoke-test)
- [x] Production content ingestion flow (index-based) implemented

## Test Gates (Release Decision Policy)

### Gate G0 — Build Integrity (hard fail)
- **Command:** `source .venv/bin/activate && pytest -q`
- **Pass criteria:** exit code `0`, no failed tests.
- **Fail criteria:** any failing test, test crash, or interrupted run.

### Gate G1 — Smoke E2E Happy Path (hard fail)
- **Scope:** `auth → course/progress → ai endpoint`.
- **Reference test:** `backend/tests/test_smoke_e2e_happy_path.py::test_smoke_e2e_happy_path_auth_course_progress_ai`
- **Pass criteria:**
  - login issues `access_token` + `refresh_token` + `csrf_token`,
  - `/api/progress` returns non-empty path (`next_lesson_id`),
  - lesson content is accessible for available lesson,
  - `/api/chat/lecture` returns `200` with `fallback_reason=ok`,
  - lesson completion increases `overall_percent`.
- **Fail criteria:** any broken step in this sequence.

### Gate G2 — Contract/Regression Baseline (hard fail)
- **Scope:** existing backend API/security/streaming/limits/contracts tests.
- **Pass criteria:** all tests in the default `pytest -q` selection are green.
- **Fail criteria:** any regression in auth, CSRF, progress logic, AI flow, limits, migrations, ops smoke.

### Gate G3 — Release Documentation Sync (hard fail)
- **Pass criteria:**
  - `docs/changelog.md` reflects delivered changes,
  - `docs/implementation-checklist.md` reflects real completion status,
  - release gates documented in this file and linked checklists/contracts.
- **Fail criteria:** code/tests changed without doc synchronization.

### Gate G4 — Frontend MVP Contract Readiness (hard fail for frontend rollout)
- **Scope:** frontend API/state/UX contracts and executable checklist.
- **Pass criteria:**
  - `docs/frontend-api-canonical.md` and `docs/frontend-state-maps.md` are synchronized,
  - `tests/checklists/frontend-readiness.checklist.md` is consistent with current frontend behavior,
  - `tests/e2e-priority-matrix.md` contains frontend smoke as P0 gate.
- **Fail criteria:** any mismatch between frontend behavior and documented contract baseline.

## Final Gate Run (2026-02-23)
- Command: `source .venv/bin/activate && pytest -q`
- Result: `52 passed, 137 warnings in 17.61s`
- Gate verdict:
  - G0 Build Integrity — **PASS**
  - G1 Smoke E2E Happy Path — **PASS**
  - G2 Contract/Regression Baseline — **PASS**
  - G3 Documentation Sync — **PASS**
  - G4 Frontend MVP Contract Readiness — **PASS**

## MVP Readiness Verdict
**MVP-ready for closed rollout.**

## Residual Known Gaps Before Wider Rollout
1. Full browser-level UI e2e (Playwright class) ещё не зафиксирован как обязательный gate; текущий baseline — frontend smoke + backend e2e.
2. Non-blocking technical debt: deprecation warnings (`FastAPI on_event`, per-request cookies in Starlette testclient) требуют плановой очистки перед production hardening wave.
3. Нужна отдельная формализация retry/backoff UX-политики для lecture reconnect при длительных сетевых обрывах.

## Additional Gate Run (2026-02-24)
- backend: `source .venv/bin/activate && pytest -q` → `52 passed`
- frontend: `cd frontend && npm run lint && npm run test && npm run build` → pass
- Verdict update: MVP frontend/backend baseline remains **PASS**.
