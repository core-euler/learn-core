import json
from typing import Iterable


def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def build_stub_stream(message_id: str, text: str = "stub stream reply", last_event_id: str | None = None) -> Iterable[str]:
    chunks = [text[:5], text[5:]] if len(text) > 5 else [text]
    if last_event_id != message_id:
        for c in chunks:
            yield sse_event({"type": "chunk", "content": c, "message_id": message_id})
    yield sse_event({"type": "done", "tokens_used": 0, "message_id": message_id})
