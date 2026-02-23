import json
from typing import Iterable


CHUNK_SIZE = 5


def sse_event(*, event_id: str, event_type: str, data: dict) -> str:
    return (
        f"id: {event_id}\n"
        f"event: {event_type}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


def _chunk_text(text: str) -> list[str]:
    if not text:
        return [""]
    return [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]


def _parse_last_event_seq(last_event_id: str | None, message_id: str, chunk_count: int) -> int:
    """
    Returns last acknowledged event sequence number for this message.

    Protocol:
    - current event ids: `<message_id>:<seq>` where seq starts from 1 for chunks,
      and `chunk_count + 1` for done.
    - backward-compatible legacy reconnect marker: `<message_id>` means
      "all chunks are already acknowledged".
    - malformed or foreign ids are ignored (treated as fresh stream).
    """
    if not last_event_id:
        return 0

    if last_event_id == message_id:
        return chunk_count

    prefix = f"{message_id}:"
    if not last_event_id.startswith(prefix):
        return 0

    seq_raw = last_event_id[len(prefix) :]
    if not seq_raw.isdigit():
        return 0

    seq = int(seq_raw)
    if seq < 0:
        return 0

    return seq


def build_text_stream(message_id: str, text: str, tokens_used: int = 0, last_event_id: str | None = None) -> Iterable[str]:
    chunks = _chunk_text(text)
    last_ack_seq = _parse_last_event_seq(last_event_id, message_id, len(chunks))

    for idx, chunk in enumerate(chunks, start=1):
        if idx <= last_ack_seq:
            continue
        event_id = f"{message_id}:{idx}"
        yield sse_event(
            event_id=event_id,
            event_type="chunk",
            data={
                "type": "chunk",
                "sequence": idx,
                "event_id": event_id,
                "content": chunk,
                "message_id": message_id,
            },
        )

    done_seq = len(chunks) + 1
    if done_seq > last_ack_seq:
        done_event_id = f"{message_id}:{done_seq}"
        yield sse_event(
            event_id=done_event_id,
            event_type="done",
            data={
                "type": "done",
                "sequence": done_seq,
                "event_id": done_event_id,
                "tokens_used": tokens_used,
                "message_id": message_id,
            },
        )
