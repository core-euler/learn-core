# LLM Handbook — MVP

Documentation-first + implementation repository for LLM Handbook MVP.

## Current status (2026-02-23)
- Backend MVP core implemented (auth/session, course/progress, AI mode scaffold, limits, Telegram auth callback).
- Alembic initialized with initial migration from current SQLAlchemy models.
- Test suite green: run `pytest -q`.
- Docker compose present (`backend + PostgreSQL`).

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

## Next focus
See: `docs/implementation-checklist.md` and `docs/release-readiness.md`.
