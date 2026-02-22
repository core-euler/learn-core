# Результат этапа 5

## Статус
В работе.

## Что реализовано
- Добавлен `user_usage` persistence слой.
- Введён дневной лимит запросов для chat endpoint-ов (`daily_limit_exceeded`).
- Введён минутный лимит (`minute_rate_limited`).
- Usage-метрики подключены к `GET /api/progress/stats`.
- Добавлен SSE-контракт для `POST /api/chat/lecture` при `Accept: text/event-stream`:
  - события `chunk`
  - событие `done`
- Добавлена базовая reconnect-логика по `Last-Event-ID`: если `Last-Event-ID == message_id`, chunk-переотправка не выполняется.

## Тесты
- Покрыты сценарии дневного и минутного лимитов в `test_ai_modes.py`.
- Покрыт SSE-контракт `lecture` и reconnect-поведение в `test_ai_modes.py`.
- Общий прогон: 18 passed.

## Ограничения
- SSE дедуп сейчас минимальный (по равенству `Last-Event-ID` и `message_id`), без полноценных event offsets.
- В production потребуется убрать/закрыть test-only endpoint `_test/reset-minute-window`.
