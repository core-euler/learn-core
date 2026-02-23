import os
import subprocess
import tempfile
from pathlib import Path

import sqlalchemy as sa


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic(database_url: str, *args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        ["alembic", *args],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _assert_core_tables_exist(database_url: str) -> None:
    engine = sa.create_engine(database_url)
    try:
        inspector = sa.inspect(engine)
        tables = set(inspector.get_table_names())
        expected = {
            "alembic_version",
            "users",
            "sessions",
            "modules",
            "lessons",
            "user_lesson_progress",
            "user_module_progress",
            "ai_sessions",
            "ai_messages",
            "user_usage",
            "user_rate_windows",
        }
        assert expected.issubset(tables)
    finally:
        engine.dispose()


def test_alembic_upgrade_and_downgrade_on_clean_sqlite_db() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "alembic_smoke.db"
        db_url = f"sqlite:///{db_path}"

        _run_alembic(db_url, "upgrade", "head")
        _assert_core_tables_exist(db_url)

        _run_alembic(db_url, "downgrade", "base")

        engine = sa.create_engine(db_url)
        try:
            inspector = sa.inspect(engine)
            tables = set(inspector.get_table_names())
            assert "users" not in tables
        finally:
            engine.dispose()


def test_alembic_upgrade_on_postgres_if_configured() -> None:
    postgres_url = os.getenv("TEST_POSTGRES_DATABASE_URL")
    if not postgres_url:
        return

    _run_alembic(postgres_url, "upgrade", "head")
    _assert_core_tables_exist(postgres_url)
