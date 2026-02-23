# Release Readiness (Closed Testing)

## Current Backend Status Snapshot
- Auth/session core: implemented
- Course/progress core: implemented
- AI provider adapter: implemented (lecture/consultant/exam wired через adapter + fallback policy)
- Minimal RAG retrieval contract: implemented (retriever interface + stub index + lecture/consultant retrieval envelope with citations)
- Streaming: basic SSE for lecture (`chunk` + `done`)
- Limits: daily + minute rate limits implemented

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

## Test Gates
- Unit/API test suite: 39 passed (`source .venv/bin/activate && pytest -q`)
- Added ops smoke checks: `backend/tests/test_ops_smoke.py` (`/healthz` + `.env.example` required keys)
- P0 E2E docs: defined
- P1 E2E docs: defined
- P2 E2E docs: defined

## Known Gaps Before Wider Rollout
1. Add SSE reconnection protocol beyond simple Last-Event-ID equality.
