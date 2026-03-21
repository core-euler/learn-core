from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .content_index import load_content_index, resolve_content_path
from .course_entities import Lesson, Module
from .progress_service import ensure_progress_for_all_users


def _pick_legacy_module(candidates: list[Module], *, title: str, order_index: int) -> Module | None:
    by_order = [row for row in candidates if row.order_index == order_index]
    if by_order:
        return by_order[0]
    by_title = [row for row in candidates if row.title == title]
    if by_title:
        return by_title[0]
    return candidates[0] if candidates else None


def _pick_legacy_lesson(
    candidates: list[Lesson],
    *,
    md_file_path: str,
    title: str,
    order_index: int,
) -> Lesson | None:
    by_path = [row for row in candidates if row.md_file_path == md_file_path]
    if by_path:
        return by_path[0]
    by_order = [row for row in candidates if row.order_index == order_index]
    if by_order:
        return by_order[0]
    by_title = [row for row in candidates if row.title == title]
    if by_title:
        return by_title[0]
    return candidates[0] if candidates else None


def sync_course_catalog_from_index(
    db: Session,
    *,
    index_path: Path,
    repo_root: Path,
) -> dict[str, int]:
    # Validate and parse source-of-truth index.
    content_index = load_content_index(index_path)

    existing_modules = db.execute(select(Module)).scalars().all()
    modules_by_slug = {module.slug: module for module in existing_modules if module.slug}
    legacy_modules = [module for module in existing_modules if not module.slug]

    active_module_ids: set[str] = set()
    active_lesson_ids: set[str] = set()

    created_modules = 0
    updated_modules = 0
    created_lessons = 0
    updated_lessons = 0

    for module_item in sorted(content_index.modules, key=lambda row: row.order_index):
        module_row = modules_by_slug.get(module_item.slug)
        if not module_row:
            module_row = _pick_legacy_module(
                legacy_modules,
                title=module_item.title,
                order_index=module_item.order_index,
            )
            if module_row:
                legacy_modules = [row for row in legacy_modules if row.id != module_row.id]

        if not module_row:
            module_row = Module(
                slug=module_item.slug,
                title=module_item.title,
                description=None,
                order_index=module_item.order_index,
                is_published=True,
            )
            db.add(module_row)
            db.flush()
            created_modules += 1
        else:
            module_row.slug = module_item.slug
            module_row.title = module_item.title
            module_row.order_index = module_item.order_index
            module_row.is_published = True
            updated_modules += 1

        modules_by_slug[module_item.slug] = module_row
        active_module_ids.add(module_row.id)

        existing_lessons = db.execute(select(Lesson).where(Lesson.module_id == module_row.id)).scalars().all()
        lessons_by_slug = {lesson.slug: lesson for lesson in existing_lessons if lesson.slug}
        legacy_lessons = [lesson for lesson in existing_lessons if not lesson.slug]

        for lesson_item in sorted(module_item.lessons, key=lambda row: row.order_index):
            # Ensure markdown file listed in index exists in repository.
            if not resolve_content_path(repo_root, lesson_item.md_file_path).exists():
                raise ValueError(f"course_sync_markdown_missing:{lesson_item.md_file_path}")

            lesson_row = lessons_by_slug.get(lesson_item.slug)
            if not lesson_row:
                lesson_row = _pick_legacy_lesson(
                    legacy_lessons,
                    md_file_path=lesson_item.md_file_path,
                    title=lesson_item.title,
                    order_index=lesson_item.order_index,
                )
                if lesson_row:
                    legacy_lessons = [row for row in legacy_lessons if row.id != lesson_row.id]

            if not lesson_row:
                lesson_row = Lesson(
                    module_id=module_row.id,
                    slug=lesson_item.slug,
                    title=lesson_item.title,
                    description=None,
                    order_index=lesson_item.order_index,
                    md_file_path=lesson_item.md_file_path,
                    is_published=True,
                )
                db.add(lesson_row)
                db.flush()
                created_lessons += 1
            else:
                lesson_row.module_id = module_row.id
                lesson_row.slug = lesson_item.slug
                lesson_row.title = lesson_item.title
                lesson_row.order_index = lesson_item.order_index
                lesson_row.md_file_path = lesson_item.md_file_path
                lesson_row.is_published = True
                updated_lessons += 1

            active_lesson_ids.add(lesson_row.id)

        for stale_lesson in existing_lessons:
            if stale_lesson.id not in active_lesson_ids:
                stale_lesson.is_published = False

    for module_row in existing_modules:
        if module_row.id not in active_module_ids:
            module_row.is_published = False
            module_lessons = db.execute(select(Lesson).where(Lesson.module_id == module_row.id)).scalars().all()
            for lesson in module_lessons:
                lesson.is_published = False

    db.commit()

    # Keep user progression compatible with updated course map.
    ensure_progress_for_all_users(db)

    return {
        "created_modules": created_modules,
        "updated_modules": updated_modules,
        "created_lessons": created_lessons,
        "updated_lessons": updated_lessons,
        "published_modules": len(active_module_ids),
        "published_lessons": len(active_lesson_ids),
    }
