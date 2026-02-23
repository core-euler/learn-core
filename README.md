# LLM Handbook — MVP

Documentation-first + implementation repository for LLM Handbook MVP.

## Current status (2026-02-23)
- Backend MVP core implemented (auth/session, course/progress, AI mode scaffold, limits, Telegram auth callback).
- Test suite green: **22 passed** (`pytest -q`).
- Docker compose present (`backend + PostgreSQL`).
- Core docs/specs/checklists populated in `docs/` and `tests/`.

## Repository map
- `backend/` — FastAPI backend implementation + tests
- `docs/` — product/architecture/spec documentation and rollout notes
- `tests/` — contracts/checklists/traceability/e2e strategy docs
- `docker-compose.yml` — local stack bootstrap

## Quick start
```bash
cd /home/claw/llm-handbook-mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Next focus
See: `docs/implementation-checklist.md` and `docs/release-readiness.md`.
