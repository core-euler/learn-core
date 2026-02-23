# Runbook (local + staging)

## 0) Preconditions

```bash
cd /home/claw/llm-handbook-mvp
cp .env.example .env
```

Adjust at minimum before shared/staging usage:
- `JWT_SECRET_KEY`
- `COOKIE_SECURE=true` for HTTPS ingress
- `POSTGRES_PASSWORD`
- `TELEGRAM_BOT_TOKEN`/`TELEGRAM_BOT_ID` if Telegram auth is enabled

---

## 1) Local run (docker compose)

### Start stack
```bash
docker compose up -d --build
```

### Wait for health
```bash
docker compose ps
# expected: db=healthy, backend=healthy
```

### Basic API smoke
```bash
curl -fsS http://localhost:8000/healthz
# expected: {"ok":true}
```

### Stop stack
```bash
docker compose down
# add -v only if you explicitly want to wipe postgres volume
```

---

## 2) Local migrations (against compose postgres)

```bash
source .venv/bin/activate
export DATABASE_URL='postgresql+psycopg://llm:llm@localhost:5432/llm_handbook'
alembic upgrade head
alembic current
```

Rollback (destructive):
```bash
alembic downgrade base
```

---

## 3) Staging runbook (single node baseline)

1. Prepare `.env` from `.env.example` with staging secrets:
   - `APP_ENV=prod`
   - strong `JWT_SECRET_KEY`
   - `COOKIE_SECURE=true`
   - non-default `POSTGRES_PASSWORD`
   - Telegram vars if Telegram login is enabled.
2. Deploy and build:
   ```bash
   docker compose --env-file .env up -d --build
   ```
3. Verify container health:
   ```bash
   docker compose ps
   ```
4. Verify backend readiness from host/network:
   ```bash
   curl -fsS http://<staging-host>:8000/healthz
   ```
5. Apply migrations (once per deploy when revision changed):
   ```bash
   source .venv/bin/activate
   export DATABASE_URL='postgresql+psycopg://<user>:<pass>@<host>:5432/<db>'
   alembic upgrade head
   alembic current
   ```

---

## 4) Test smoke checks

```bash
source .venv/bin/activate
pytest -q
```

Targeted migration smoke:
```bash
pytest -q backend/tests/test_alembic_migrations.py
```

Optional PostgreSQL migration smoke:
```bash
export TEST_POSTGRES_DATABASE_URL='postgresql+psycopg://llm:llm@localhost:5432/llm_handbook'
pytest -q backend/tests/test_alembic_migrations.py
```
