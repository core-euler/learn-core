# Результат этапа 4

## Статус
В работе.

## Что реализовано
- Добавлены сущности `ai_sessions` и `ai_messages`.
- Реализован backend scaffold endpoints:
  - `POST /api/chat/lecture`
  - `POST /api/chat/exam/start`
  - `POST /api/chat/exam/finish`
  - `POST /api/chat/consultant`
  - `GET /api/chat/sessions`
  - `GET /api/chat/sessions/{session_id}`
- Реализованы режимные access-check правила:
  - lecture/exam только для available/completed уроков,
  - consultant только после completed модуля.
- Реализован базовый exam lifecycle: start -> finish с pass/fail и обновлением прогресса.

## Тесты
- Добавлен и расширен `backend/tests/test_ai_modes.py`.
- Общий прогон: 16 passed.

## Ограничения
- Ответы AI пока stub-уровня (без реального LLM/RAG pipeline).
- SSE stream в следующем инкременте phase-5.
