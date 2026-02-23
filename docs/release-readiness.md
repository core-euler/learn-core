# Release Readiness (Closed Testing)

## Current Backend Status Snapshot
- Auth/session core: implemented
- Course/progress core: implemented
- AI scaffold + exam lifecycle: implemented (stub LLM responses)
- Streaming: basic SSE for lecture (`chunk` + `done`)
- Limits: daily + minute rate limits implemented

## Security/Hardening Checklist
- [x] httpOnly auth cookies
- [x] Configurable cookie flags (`secure`, `samesite`) via env
- [x] Test-only endpoints restricted to `APP_ENV=test` (+ smoke in prod-like env)
- [x] CSRF protection (double-submit) for state-changing endpoints
- [x] Telegram OAuth cryptographic validation: HMAC + freshness + bot-id binding
- [ ] Password hashing policy upgrade for production KDF

## Data/Infra Checklist
- [x] Docker compose with PostgreSQL + backend
- [x] SQLAlchemy persistence in place
- [ ] Alembic migrations introduced
- [ ] Production content ingestion flow (index-based) implemented

## Test Gates
- Unit/API test suite: 28 passed (`.venv/bin/pytest -q`)
- P0 E2E docs: defined
- P1 E2E docs: defined
- P2 E2E docs: defined

## Known Gaps Before Wider Rollout
1. Replace stub AI replies with real LLM+RAG pipeline.
2. Add SSE reconnection protocol beyond simple Last-Event-ID equality.
3. Add production-grade password/KDF policy and migration path.
