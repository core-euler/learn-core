from backend.app.retrieval import (
    ChunkMetadata,
    RetrievedChunk,
    RetrievalQuery,
    StubChunkIndex,
    StubRetriever,
)


def _chunk(*, chunk_id: str, lesson_id: str, text: str, score: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        metadata=ChunkMetadata(
            chunk_id=chunk_id,
            module_id="m1",
            lesson_id=lesson_id,
            source_path=f"content/{lesson_id}.md",
            start_char=0,
            end_char=len(text),
        ),
        text=text,
        score=score,
    )


def test_stub_retriever_returns_top_k_with_citations_for_lesson_scope() -> None:
    retriever = StubRetriever(
        StubChunkIndex(
            [
                _chunk(chunk_id="c1", lesson_id="l1", text="Neural network basics and perceptron"),
                _chunk(chunk_id="c2", lesson_id="l1", text="Gradient descent and loss functions"),
                _chunk(chunk_id="c3", lesson_id="l2", text="Databases and SQL joins"),
            ]
        )
    )

    result = retriever.retrieve(
        RetrievalQuery(user_id="u1", mode="lecture", lesson_id="l1", message="gradient neural", top_k=1)
    )

    assert len(result.chunks) == 1
    assert result.chunks[0].metadata.lesson_id == "l1"
    assert len(result.citations) == 1
    assert result.citations[0].chunk_id == result.chunks[0].metadata.chunk_id
    assert result.citations[0].source_path == "content/l1.md"


def test_stub_retriever_returns_empty_when_top_k_is_zero() -> None:
    retriever = StubRetriever(StubChunkIndex([_chunk(chunk_id="c1", lesson_id="l1", text="Any content")]))

    result = retriever.retrieve(
        RetrievalQuery(user_id="u1", mode="consultant", lesson_id=None, message="content", top_k=0)
    )

    assert result.chunks == []
    assert result.citations == []
