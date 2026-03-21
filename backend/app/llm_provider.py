from __future__ import annotations

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
import json
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest


class LlmProviderError(Exception):
    pass


@dataclass
class LlmReply:
    text: str
    tokens_used: int = 0
    provider: str = "default"


class LlmProviderAdapter(ABC):
    @abstractmethod
    def lecture_reply(self, *, lesson_id: str, message: str, message_id: str) -> LlmReply:
        raise NotImplementedError

    @abstractmethod
    def consultant_reply(self, *, message: str, message_id: str) -> LlmReply:
        raise NotImplementedError

    @abstractmethod
    def build_exam(self, *, lesson_id: str) -> dict[str, Any]:
        raise NotImplementedError


class DefaultLlmProviderAdapter(LlmProviderAdapter):
    """Deterministic local implementation used as runtime-safe default."""

    def lecture_reply(self, *, lesson_id: str, message: str, message_id: str) -> LlmReply:
        text = f"[lecture:{lesson_id}] {message.strip() or '...' }"
        return LlmReply(text=text, tokens_used=max(1, len(message.split())), provider="default")

    def consultant_reply(self, *, message: str, message_id: str) -> LlmReply:
        text = f"[consultant] {message.strip() or '...' }"
        return LlmReply(text=text, tokens_used=max(1, len(message.split())), provider="default")

    def build_exam(self, *, lesson_id: str) -> dict[str, Any]:
        questions = [
            {'id': 1, 'type': 'multiple_choice', 'text': f'{lesson_id}: Q1', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A'},
            {'id': 2, 'type': 'multiple_choice', 'text': f'{lesson_id}: Q2', 'options': ['A', 'B', 'C', 'D'], 'answer': 'B'},
            {'id': 3, 'type': 'multiple_choice', 'text': f'{lesson_id}: Q3', 'options': ['A', 'B', 'C', 'D'], 'answer': 'C'},
            {'id': 4, 'type': 'open', 'text': f'{lesson_id}: Q4', 'answer': 'open'},
            {'id': 5, 'type': 'open', 'text': f'{lesson_id}: Q5', 'answer': 'open'},
        ]
        return {'questions': questions, 'provider': 'default'}


class CometApiLlmProviderAdapter(LlmProviderAdapter):
    """CometAPI-based adapter using OpenAI-compatible /v1/chat/completions."""

    def __init__(self, *, api_key: str, base_url: str, chat_model: str, exam_model: str):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._chat_model = chat_model
        self._exam_model = exam_model

    def lecture_reply(self, *, lesson_id: str, message: str, message_id: str) -> LlmReply:
        payload = {
            "model": self._chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an educational lecture assistant. "
                        "Answer clearly and concisely based only on provided lesson context and user question."
                    ),
                },
                {
                    "role": "user",
                    "content": f"lesson_id={lesson_id}\nmessage={message}",
                },
            ],
        }
        resp = self._post_json("/v1/chat/completions", payload)
        text = self._extract_chat_text(resp)
        tokens = self._extract_total_tokens(resp)
        return LlmReply(text=text, tokens_used=tokens, provider="cometapi")

    def consultant_reply(self, *, message: str, message_id: str) -> LlmReply:
        payload = {
            "model": self._chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a consultant assistant for a learning platform. "
                        "Give practical, correct answers, and avoid unsupported claims."
                    ),
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
        }
        resp = self._post_json("/v1/chat/completions", payload)
        text = self._extract_chat_text(resp)
        tokens = self._extract_total_tokens(resp)
        return LlmReply(text=text, tokens_used=tokens, provider="cometapi")

    def build_exam(self, *, lesson_id: str) -> dict[str, Any]:
        prompt = (
            "Return ONLY valid JSON with shape: "
            "{\"questions\":[{" \
            "\"id\":1,\"type\":\"multiple_choice\",\"text\":\"...\",\"options\":[\"A\",\"B\",\"C\",\"D\"],\"answer\":\"A\"}," \
            "{\"id\":2,\"type\":\"multiple_choice\",\"text\":\"...\",\"options\":[\"A\",\"B\",\"C\",\"D\"],\"answer\":\"B\"}," \
            "{\"id\":3,\"type\":\"multiple_choice\",\"text\":\"...\",\"options\":[\"A\",\"B\",\"C\",\"D\"],\"answer\":\"C\"}," \
            "{\"id\":4,\"type\":\"open\",\"text\":\"...\",\"answer\":\"open\"}," \
            "{\"id\":5,\"type\":\"open\",\"text\":\"...\",\"answer\":\"open\"}]}. "
            "Generate exam questions for lesson_id="
            f"{lesson_id}."
        )
        payload = {
            "model": self._exam_model,
            "messages": [
                {"role": "system", "content": "You are an exam generator for a learning platform."},
                {"role": "user", "content": prompt},
            ],
        }
        resp = self._post_json("/v1/chat/completions", payload)
        text = self._extract_chat_text(resp)
        parsed = self._extract_exam_json(text)
        questions = parsed.get("questions") if isinstance(parsed, dict) else None
        if not isinstance(questions, list) or len(questions) == 0:
            raise LlmProviderError("invalid_exam_payload")
        return {"questions": questions, "provider": "cometapi"}

    def embed_texts(self, *, model: str, inputs: list[str]) -> dict[str, Any]:
        """OpenAI-compatible embeddings call for future retrieval integration."""
        payload = {
            "model": model,
            "input": inputs,
        }
        return self._post_json("/v1/embeddings", payload)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlrequest.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urlerror.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LlmProviderError(f"cometapi_http_error:{exc.code}:{detail[:200]}") from exc
        except urlerror.URLError as exc:
            raise LlmProviderError(f"cometapi_connection_error:{exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LlmProviderError("cometapi_invalid_json") from exc
        if not isinstance(data, dict):
            raise LlmProviderError("cometapi_invalid_payload")
        return data

    def _extract_chat_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LlmProviderError("cometapi_missing_choices")
        first = choices[0] if isinstance(choices[0], dict) else {}
        msg = first.get("message") if isinstance(first, dict) else {}
        if not isinstance(msg, dict):
            raise LlmProviderError("cometapi_missing_message")
        content = msg.get("content", "")

        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            text = "\n".join(parts).strip()
        else:
            text = ""

        if not text:
            raise LlmProviderError("cometapi_empty_content")
        return text

    def _extract_total_tokens(self, payload: dict[str, Any]) -> int:
        usage = payload.get("usage")
        if isinstance(usage, dict):
            total = usage.get("total_tokens")
            if isinstance(total, int) and total >= 0:
                return total
        return 0

    def _extract_exam_json(self, text: str) -> dict[str, Any]:
        text = text.strip()

        # Handle common markdown fenced JSON format.
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
                text = "\n".join(lines[1:-1]).strip()
                if text.startswith("json"):
                    text = text[len("json") :].strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LlmProviderError("exam_json_not_found")

        candidate = text[start : end + 1]
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise LlmProviderError("exam_json_invalid") from exc

        if not isinstance(data, dict):
            raise LlmProviderError("exam_json_invalid_shape")
        return data


@dataclass
class LlmPolicy:
    timeout_seconds: float = 8.0
    fallback_lecture: str = "Сервис AI временно недоступен. Попробуй ещё раз через минуту."
    fallback_consultant: str = "Консультант временно недоступен. Попробуй повторить запрос позже."


def build_llm_adapter(*, provider: str, comet_api_key: str, comet_base_url: str, comet_chat_model: str, comet_exam_model: str) -> LlmProviderAdapter:
    if provider == "cometapi" and comet_api_key:
        return CometApiLlmProviderAdapter(
            api_key=comet_api_key,
            base_url=comet_base_url,
            chat_model=comet_chat_model,
            exam_model=comet_exam_model,
        )
    return DefaultLlmProviderAdapter()


def call_with_fallback(*, fn, timeout_seconds: float, fallback_text: str) -> tuple[LlmReply, bool, str]:
    """Execute provider call with timeout/error fallback.

    Returns: (reply, is_fallback, reason)
    reason in {"ok", "timeout", "error"}
    """
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            reply = future.result(timeout=timeout_seconds)
            return reply, False, "ok"
        except FutureTimeoutError:
            return LlmReply(text=fallback_text, provider="fallback"), True, "timeout"
        except Exception:
            return LlmReply(text=fallback_text, provider="fallback"), True, "error"
