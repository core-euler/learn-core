# LLM Handbook — MVP

Documentation-first + implementation repository for LLM Handbook MVP.

## Current status (2026-03-05)
- MVP backend scope implemented (auth/session, course/progress, AI modes via provider adapter + minimal RAG contract, SSE reliability, limits, Telegram auth callback).
- MVP frontend app shell implemented (`frontend/`, Vite + React + TS): auth routes, protected app shell, dashboard, modules/lessons states, lesson workspace with lecture/exam/consultant flows, limits/error mapping.
- Security hardening baseline закрыт: CSRF double-submit, test-route isolation, production KDF policy.
- Alembic initialized with initial migration from current SQLAlchemy models.
- Release test gate green: backend `52 passed` + frontend smoke (`vitest`, 2 passed).
- Docker compose present (`backend + PostgreSQL`) с healthchecks.

## Repository map
- `backend/` — FastAPI backend implementation + tests
- `alembic/` — DB migrations
- `docs/` — product/architecture/spec documentation and rollout notes
- `tests/` — contracts/checklists/traceability/e2e strategy docs
- `docker-compose.yml` — local stack bootstrap

## Quick start
```bash
cd /home/claw/llm-handbook-mvp
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Frontend local shell
```bash
cd /home/claw/llm-handbook-mvp/frontend
npm install
npm run dev
# optional: VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Docker local stack
```bash
docker compose up -d --build
docker compose ps  # db/backend should become healthy
curl -fsS http://localhost:8000/healthz
```

Local/staging operational steps: `docs/runbook.md`.

## DB migrations (Alembic)
```bash
# uses DATABASE_URL if set, otherwise sqlite:///./backend_dev.db
alembic upgrade head
alembic downgrade base
alembic current
alembic history
```

For clean PostgreSQL bootstrap, see `docs/runbook.md`.

## Release status
MVP-ready for closed rollout по зафиксированным quality gates (см. `docs/release-readiness.md`).

Residual known gaps перед wider rollout:
- full browser-level UI e2e (Playwright-класс) ещё не зафиксирован как обязательный release gate;
- есть non-blocking технический долг по deprecation warnings (FastAPI `on_event`, per-request cookies в testclient).
