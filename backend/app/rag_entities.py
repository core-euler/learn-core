from datetime import datetime, timezone
import uuid

from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class RagChunk(Base):
    __tablename__ = "rag_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_signature: Mapped[str] = mapped_column(String(64), index=True)
    chunk_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    module_id: Mapped[str] = mapped_column(String(255), index=True)
    lesson_id: Mapped[str] = mapped_column(String(255), index=True)
    source_path: Mapped[str] = mapped_column(String(1000), index=True)
    start_char: Mapped[int] = mapped_column(Integer)
    end_char: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RagIndexState(Base):
    __tablename__ = "rag_index_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    content_signature: Mapped[str] = mapped_column(String(64), index=True)
    embed_model: Mapped[str] = mapped_column(String(255))
    chunk_size_chars: Mapped[int] = mapped_column(Integer)
    chunk_overlap_chars: Mapped[int] = mapped_column(Integer)
    embeddings_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
