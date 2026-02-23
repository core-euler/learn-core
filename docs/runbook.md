# Runbook (local/staging basics)

## DB migrations

### 1) Apply latest migration
```bash
cd /home/claw/llm-handbook-mvp
source .venv/bin/activate
export DATABASE_URL='postgresql+psycopg://llm:llm@localhost:5432/llm_handbook'
alembic upgrade head
```

### 2) Check migration status
```bash
alembic current
alembic history
```

### 3) Rollback to base (dangerous, destroys schema objects)
```bash
alembic downgrade base
```

## Clean bootstrap in empty PostgreSQL

Prereq: running PostgreSQL and empty target database.

```bash
# Example with docker-compose service "db" from this repo
# 1. start postgres
cd /home/claw/llm-handbook-mvp
docker compose up -d db

# 2. run migrations into empty DB
source .venv/bin/activate
export DATABASE_URL='postgresql+psycopg://llm:llm@localhost:5432/llm_handbook'
alembic upgrade head

# 3. verify revision
alembic current
```

## Smoke-check via pytest

```bash
# always runs sqlite migration smoke
pytest -q backend/tests/test_alembic_migrations.py

# optional postgres smoke if URL is provided
export TEST_POSTGRES_DATABASE_URL='postgresql+psycopg://llm:llm@localhost:5432/llm_handbook'
pytest -q backend/tests/test_alembic_migrations.py
```
