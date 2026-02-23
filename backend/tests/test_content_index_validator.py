import json
from pathlib import Path

import pytest

from backend.app.content_index import validate_content_index, validate_default_content_index


def _write_index(tmp_path: Path, payload: dict) -> Path:
    content_dir = tmp_path / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    index_path = content_dir / "index.json"
    index_path.write_text(json.dumps(payload), encoding="utf-8")
    return index_path


def _valid_payload() -> dict:
    return {
        "version": "2026-02-23",
        "modules": [
            {
                "slug": "m1",
                "title": "M1",
                "order_index": 1,
                "lessons": [
                    {
                        "slug": "l1",
                        "title": "L1",
                        "order_index": 1,
                        "md_file_path": "content/m1/l1.md",
                    }
                ],
            }
        ],
    }


def test_default_content_index_is_valid():
    validate_default_content_index()


def test_content_index_fails_when_lesson_file_missing(tmp_path: Path):
    index_path = _write_index(tmp_path, _valid_payload())

    with pytest.raises(ValueError, match="content_index_md_missing"):
        validate_content_index(index_path, repo_root=tmp_path)


def test_content_index_fails_when_module_without_lessons(tmp_path: Path):
    payload = _valid_payload()
    payload["modules"][0]["lessons"] = []

    index_path = _write_index(tmp_path, payload)
    with pytest.raises(ValueError, match="content_index_module_without_lessons"):
        validate_content_index(index_path, repo_root=tmp_path)


def test_content_index_fails_when_contract_field_missing(tmp_path: Path):
    payload = _valid_payload()
    del payload["version"]
    (tmp_path / "content" / "m1").mkdir(parents=True)
    (tmp_path / "content" / "m1" / "l1.md").write_text("# ok", encoding="utf-8")

    index_path = _write_index(tmp_path, payload)
    with pytest.raises(ValueError, match="content_index_schema_error"):
        validate_content_index(index_path, repo_root=tmp_path)
