# Результат этапа 4

## Статус
В работе.

## Что реализовано
- Добавлены сущности `ai_sessions` и `ai_messages`.
- Реализован backend scaffold endpoints:
  - `POST /api/chat/lecture`
  - `POST /api/chat/exam/start`
  - `POST /api/chat/consultant`
- Реализованы режимные access-check правила:
  - lecture/exam только для available/completed уроков,
  - consultant только после completed модуля.

## Тесты
- Добавлен `backend/tests/test_ai_modes.py`.
- Общий прогон: 15 passed.

## Ограничения
- Ответы AI пока stub-уровня (без реального LLM/RAG pipeline).
- SSE stream и детальный exam lifecycle в следующем инкременте phase-4/5.
