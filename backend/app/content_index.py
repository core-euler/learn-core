from __future__ import annotations

from pathlib import Path
from typing import List
import json

from pydantic import BaseModel, Field, ValidationError


class ContentLesson(BaseModel):
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    order_index: int = Field(ge=1)
    md_file_path: str = Field(min_length=1)
    type: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)
    prerequisites: List[str]
    tags: List[str]


class ContentModule(BaseModel):
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    order_index: int = Field(ge=1)
    full_chapter: str = Field(min_length=1)
    lessons: List[ContentLesson]


class ContentIndex(BaseModel):
    version: str = Field(min_length=1)
    modules: List[ContentModule]


def _read_index(index_path: Path) -> dict:
    if not index_path.exists():
        raise ValueError(f"content_index_not_found: {index_path}")
    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"content_index_invalid_json: {exc}") from exc


def load_content_index(index_path: Path) -> ContentIndex:
    raw = _read_index(index_path)
    try:
        return ContentIndex.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"content_index_schema_error: {exc}") from exc


def normalize_content_rel_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("content/"):
        normalized = normalized[len("content/") :]
    if not normalized:
        raise ValueError("content_index_empty_rel_path")
    if normalized.startswith("/"):
        raise ValueError(f"content_index_absolute_path_forbidden: {path}")
    candidate = Path(normalized)
    if ".." in candidate.parts:
        raise ValueError(f"content_index_parent_path_forbidden: {path}")
    return normalized


def resolve_content_path(repo_root: Path, path: str) -> Path:
    rel = normalize_content_rel_path(path)
    content_root = (repo_root / "content").resolve()
    abs_path = (content_root / rel).resolve()
    if content_root != abs_path and content_root not in abs_path.parents:
        raise ValueError(f"content_index_path_escape_forbidden: {path}")
    return abs_path


def validate_content_index(index_path: Path, repo_root: Path | None = None) -> None:
    content_index = load_content_index(index_path)
    root = repo_root or index_path.parent.parent

    if not content_index.modules:
        raise ValueError("content_index_empty_modules")

    module_slugs: set[str] = set()
    module_order: set[int] = set()
    lesson_slug_count: dict[str, int] = {}

    for module in content_index.modules:
        if module.slug in module_slugs:
            raise ValueError(f"content_index_duplicate_module_slug: {module.slug}")
        module_slugs.add(module.slug)

        if module.order_index in module_order:
            raise ValueError(f"content_index_duplicate_module_order: {module.order_index}")
        module_order.add(module.order_index)

        chapter_path = resolve_content_path(root, module.full_chapter)
        if not chapter_path.exists():
            raise ValueError(
                f"content_index_full_chapter_missing: {module.slug} -> {module.full_chapter}"
            )

        if not module.lessons:
            raise ValueError(f"content_index_module_without_lessons: {module.slug}")

        lesson_slugs: set[str] = set()
        lesson_order: set[int] = set()
        for lesson in module.lessons:
            if lesson.slug in lesson_slugs:
                raise ValueError(
                    f"content_index_duplicate_lesson_slug: {module.slug}/{lesson.slug}"
                )
            lesson_slugs.add(lesson.slug)
            lesson_slug_count[lesson.slug] = lesson_slug_count.get(lesson.slug, 0) + 1

            if lesson.order_index in lesson_order:
                raise ValueError(
                    f"content_index_duplicate_lesson_order: {module.slug}/{lesson.order_index}"
                )
            lesson_order.add(lesson.order_index)

            md_path = resolve_content_path(root, lesson.md_file_path)
            if not md_path.exists():
                raise ValueError(
                    f"content_index_md_missing: {module.slug}/{lesson.slug} -> {lesson.md_file_path}"
                )

            if any(not prereq.strip() for prereq in lesson.prerequisites):
                raise ValueError(f"content_index_invalid_prerequisite_value: {module.slug}/{lesson.slug}")
            if any(not tag.strip() for tag in lesson.tags):
                raise ValueError(f"content_index_invalid_tag_value: {module.slug}/{lesson.slug}")

    for module in content_index.modules:
        for lesson in module.lessons:
            for prereq_slug in lesson.prerequisites:
                count = lesson_slug_count.get(prereq_slug, 0)
                if count == 0:
                    raise ValueError(
                        f"content_index_unknown_prerequisite: {module.slug}/{lesson.slug} -> {prereq_slug}"
                    )
                if count > 1:
                    raise ValueError(
                        f"content_index_ambiguous_prerequisite: {module.slug}/{lesson.slug} -> {prereq_slug}"
                    )
                if prereq_slug == lesson.slug:
                    raise ValueError(
                        f"content_index_self_prerequisite: {module.slug}/{lesson.slug}"
                    )


def default_index_path() -> Path:
    return (Path(__file__).resolve().parent.parent / "content" / "index.json").resolve()


def validate_default_content_index() -> None:
    validate_content_index(default_index_path(), repo_root=Path(__file__).resolve().parent.parent)


if __name__ == "__main__":
    try:
        validate_default_content_index()
    except Exception as exc:
        print(f"[content-validate] failed: {exc}")
        raise SystemExit(1)
    print("[content-validate] ok")
