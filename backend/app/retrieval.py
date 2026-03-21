from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Callable, Sequence
import math

from .content_index import ContentIndex, load_content_index


@dataclass(frozen=True)
class ChunkMetadata:
    chunk_id: str
    module_id: str
    lesson_id: str
    source_path: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class RetrievedChunk:
    metadata: ChunkMetadata
    text: str
    score: float


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    lesson_id: str
    source_path: str
    quote: str


@dataclass(frozen=True)
class RetrievalQuery:
    user_id: str
    mode: str
    message: str
    top_k: int
    lesson_id: str | None = None
    lesson_source_path: str | None = None
    allowed_source_paths: list[str] | None = None


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]
    citations: list[Citation]


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        raise NotImplementedError


@dataclass(frozen=True)
class EmbeddedChunk:
    metadata: ChunkMetadata
    text: str
    embedding: list[float] | None = None


class StubChunkIndex:
    """In-memory index stub for contract-level RAG integration."""

    def __init__(self, chunks: list[RetrievedChunk] | None = None):
        self._chunks = list(chunks or [])

    @classmethod
    def empty(cls) -> "StubChunkIndex":
        return cls(chunks=[])

    def all_chunks(self) -> list[RetrievedChunk]:
        return list(self._chunks)


class StubRetriever(Retriever):
    """Minimal retriever stub.

    Behavior:
    - filters by lesson_id for lecture/exam modes
    - for consultant mode searches all indexed chunks
    - ranks by simple token overlap with deterministic tie-break
    - returns at most top_k chunks and derived citations
    """

    def __init__(self, index: StubChunkIndex):
        self._index = index

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        if query.top_k <= 0:
            return RetrievalResult(chunks=[], citations=[])

        candidates = self._index.all_chunks()
        if query.mode in {"lecture", "exam"}:
            if query.lesson_source_path:
                candidates = [c for c in candidates if c.metadata.source_path == query.lesson_source_path]
            elif query.lesson_id:
                candidates = [c for c in candidates if c.metadata.lesson_id == query.lesson_id]

        if query.allowed_source_paths is not None:
            allowed = set(query.allowed_source_paths)
            candidates = [c for c in candidates if c.metadata.source_path in allowed]

        tokens = {t.lower() for t in query.message.split() if t.strip()}

        scored: list[tuple[int, RetrievedChunk]] = []
        for chunk in candidates:
            if not tokens:
                overlap = 0
            else:
                overlap = sum(1 for token in tokens if token in chunk.text.lower())
            scored.append((overlap, chunk))

        scored.sort(
            key=lambda row: (
                row[0],
                row[1].score,
                row[1].metadata.chunk_id,
            ),
            reverse=True,
        )

        selected = [chunk for overlap, chunk in scored if overlap > 0][: query.top_k]
        citations = [
            Citation(
                chunk_id=chunk.metadata.chunk_id,
                lesson_id=chunk.metadata.lesson_id,
                source_path=chunk.metadata.source_path,
                quote=chunk.text[:180],
            )
            for chunk in selected
        ]
        return RetrievalResult(chunks=selected, citations=citations)


class CurriculumEmbeddingRetriever(Retriever):
    """Retriever backed by curriculum chunks with optional embedding similarity."""

    def __init__(
        self,
        *,
        chunks: list[EmbeddedChunk],
        embed_texts: Callable[[list[str]], list[list[float]]] | None = None,
    ):
        self._chunks = chunks
        self._embed_texts = embed_texts

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        if query.top_k <= 0:
            return RetrievalResult(chunks=[], citations=[])

        candidates = list(self._chunks)
        if query.mode in {"lecture", "exam"}:
            if query.lesson_source_path:
                candidates = [c for c in candidates if c.metadata.source_path == query.lesson_source_path]
            elif query.lesson_id:
                candidates = [c for c in candidates if c.metadata.lesson_id == query.lesson_id]

        if query.allowed_source_paths is not None:
            allowed = set(query.allowed_source_paths)
            candidates = [c for c in candidates if c.metadata.source_path in allowed]

        if not candidates:
            return RetrievalResult(chunks=[], citations=[])

        ranked = self._rank_candidates(candidates, query.message)
        selected = ranked[: query.top_k]
        citations = [
            Citation(
                chunk_id=chunk.metadata.chunk_id,
                lesson_id=chunk.metadata.lesson_id,
                source_path=chunk.metadata.source_path,
                quote=chunk.text[:180],
            )
            for chunk in selected
        ]
        return RetrievalResult(chunks=selected, citations=citations)

    def _rank_candidates(self, chunks: list[EmbeddedChunk], message: str) -> list[RetrievedChunk]:
        if self._embed_texts:
            try:
                message_vecs = self._embed_texts([message])
                if message_vecs and message_vecs[0]:
                    query_vec = _normalize_vector(message_vecs[0])
                    with_scores: list[tuple[float, EmbeddedChunk]] = []
                    for chunk in chunks:
                        if not chunk.embedding:
                            continue
                        score = _cosine_similarity(query_vec, chunk.embedding)
                        with_scores.append((score, chunk))
                    if with_scores:
                        with_scores.sort(
                            key=lambda row: (
                                row[0],
                                row[1].metadata.chunk_id,
                            ),
                            reverse=True,
                        )
                        return [
                            RetrievedChunk(metadata=chunk.metadata, text=chunk.text, score=score)
                            for score, chunk in with_scores
                        ]
            except Exception:
                # Fall back to lexical ranking when embeddings are unavailable or provider fails.
                pass

        tokens = {t.lower() for t in message.split() if t.strip()}
        scored: list[tuple[int, EmbeddedChunk]] = []
        for chunk in chunks:
            overlap = sum(1 for token in tokens if token in chunk.text.lower()) if tokens else 0
            scored.append((overlap, chunk))
        scored.sort(
            key=lambda row: (
                row[0],
                row[1].metadata.chunk_id,
            ),
            reverse=True,
        )
        return [
            RetrievedChunk(metadata=chunk.metadata, text=chunk.text, score=float(overlap))
            for overlap, chunk in scored
            if overlap > 0
        ]


def _chunk_markdown(text: str, *, chunk_size: int, overlap: int) -> list[tuple[int, int, str]]:
    if not text:
        return [(0, 0, "")]

    if chunk_size <= 0:
        return [(0, len(text), text)]

    chunks: list[tuple[int, int, str]] = []
    cursor = 0
    text_len = len(text)
    while cursor < text_len:
        end = min(text_len, cursor + chunk_size)
        chunks.append((cursor, end, text[cursor:end]))
        if end >= text_len:
            break
        cursor = max(0, end - overlap)
    return chunks


def _normalize_vector(vec: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return [0.0 for _ in vec]
    return [float(v) / norm for v in vec]


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


def compute_curriculum_content_signature(
    *,
    index_path: Path,
    repo_root: Path,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
    embed_model: str,
) -> str:
    hasher = hashlib.sha256()
    hasher.update(f"chunk_size_chars={chunk_size_chars}\n".encode("utf-8"))
    hasher.update(f"chunk_overlap_chars={chunk_overlap_chars}\n".encode("utf-8"))
    hasher.update(f"embed_model={embed_model}\n".encode("utf-8"))
    hasher.update(index_path.read_bytes())

    content_index: ContentIndex = load_content_index(index_path)
    for module in content_index.modules:
        for lesson in module.lessons:
            source_path = lesson.md_file_path
            hasher.update(source_path.encode("utf-8"))
            hasher.update(b"\0")

            md_abs = (repo_root / source_path).resolve()
            if not md_abs.exists():
                hasher.update(b"__MISSING__")
                hasher.update(b"\0")
                continue
            hasher.update(md_abs.read_bytes())
            hasher.update(b"\0")

    return hasher.hexdigest()


def load_curriculum_chunks(
    *,
    index_path: Path,
    repo_root: Path,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
) -> list[EmbeddedChunk]:
    content_index: ContentIndex = load_content_index(index_path)
    embedded_chunks: list[EmbeddedChunk] = []

    for module in content_index.modules:
        for lesson in module.lessons:
            source_path = lesson.md_file_path
            md_abs = (repo_root / source_path).resolve()
            if not md_abs.exists():
                continue
            text = md_abs.read_text(encoding="utf-8")
            raw_chunks = _chunk_markdown(
                text,
                chunk_size=chunk_size_chars,
                overlap=chunk_overlap_chars,
            )
            for idx, (start_char, end_char, chunk_text) in enumerate(raw_chunks, start=1):
                chunk_id = f"{module.slug}:{lesson.slug}:{idx}"
                embedded_chunks.append(
                    EmbeddedChunk(
                        metadata=ChunkMetadata(
                            chunk_id=chunk_id,
                            module_id=module.slug,
                            lesson_id=lesson.slug,
                            source_path=source_path,
                            start_char=start_char,
                            end_char=end_char,
                        ),
                        text=chunk_text,
                        embedding=None,
                    )
                )
    return embedded_chunks


def embed_curriculum_chunks(
    *,
    chunks: list[EmbeddedChunk],
    embed_texts: Callable[[list[str]], list[list[float]]] | None,
    embedding_batch_size: int,
) -> tuple[list[EmbeddedChunk], bool]:
    if not chunks or not embed_texts:
        return chunks, False
    try:
        texts = [chunk.text for chunk in chunks]
        vectors: list[list[float]] = []
        for i in range(0, len(texts), embedding_batch_size):
            batch = texts[i : i + embedding_batch_size]
            batch_vectors = embed_texts(batch)
            vectors.extend(batch_vectors)

        if len(vectors) != len(chunks):
            return chunks, False

        embedded = [
            EmbeddedChunk(
                metadata=chunk.metadata,
                text=chunk.text,
                embedding=_normalize_vector(vectors[idx]) if vectors[idx] else None,
            )
            for idx, chunk in enumerate(chunks)
        ]
        embeddings_ready = any(chunk.embedding for chunk in embedded)
        return embedded, embeddings_ready
    except Exception:
        # Keep lexical fallback when embeddings provider is unavailable.
        return chunks, False


def build_retriever_from_embedded_chunks(
    *,
    chunks: list[EmbeddedChunk],
    embed_texts: Callable[[list[str]], list[list[float]]] | None = None,
) -> Retriever:
    if not chunks:
        return StubRetriever(StubChunkIndex.empty())
    runtime_embed_texts = embed_texts if any(chunk.embedding for chunk in chunks) else None
    return CurriculumEmbeddingRetriever(chunks=chunks, embed_texts=runtime_embed_texts)


def build_curriculum_embedding_retriever(
    *,
    index_path: Path,
    repo_root: Path,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
    embed_texts: Callable[[list[str]], list[list[float]]] | None = None,
    embedding_batch_size: int = 32,
) -> Retriever:
    chunks = load_curriculum_chunks(
        index_path=index_path,
        repo_root=repo_root,
        chunk_size_chars=chunk_size_chars,
        chunk_overlap_chars=chunk_overlap_chars,
    )
    chunks, _ = embed_curriculum_chunks(
        chunks=chunks,
        embed_texts=embed_texts,
        embedding_batch_size=embedding_batch_size,
    )
    return build_retriever_from_embedded_chunks(chunks=chunks, embed_texts=embed_texts)
