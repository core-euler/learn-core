from datetime import datetime, timezone
import uuid

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("modules.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, index=True)
    md_file_path: Mapped[str] = mapped_column(String(1000))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="locked")
    exam_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exam_attempts: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserModuleProgress(Base):
    __tablename__ = "user_module_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("modules.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="locked")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
