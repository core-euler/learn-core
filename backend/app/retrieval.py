from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


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


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]
    citations: list[Citation]


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        raise NotImplementedError


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
        if query.mode in {"lecture", "exam"} and query.lesson_id:
            candidates = [c for c in candidates if c.metadata.lesson_id == query.lesson_id]

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
