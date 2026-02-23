from __future__ import annotations

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from typing import Any


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
    """Default provider implementation.

    Deterministic local implementation used as runtime default until external LLM
    provider wiring is introduced.
    """

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


@dataclass
class LlmPolicy:
    timeout_seconds: float = 8.0
    fallback_lecture: str = "Сервис AI временно недоступен. Попробуй ещё раз через минуту."
    fallback_consultant: str = "Консультант временно недоступен. Попробуй повторить запрос позже."


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
