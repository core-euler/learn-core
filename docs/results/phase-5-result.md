# Результат этапа 5

## Статус
В работе.

## Что реализовано
- Добавлен `user_usage` persistence слой.
- Введён базовый дневной лимит запросов для chat endpoint-ов (`daily_limit_exceeded`).
- Usage-метрики подключены к `GET /api/progress/stats`.
- Добавлен базовый SSE-контракт для `POST /api/chat/lecture` при `Accept: text/event-stream`:
  - события `chunk`
  - событие `done`

## Тесты
- Покрыт сценарий лимита в `test_ai_modes.py`.
- Покрыт базовый SSE-контракт `lecture` в `test_ai_modes.py`.

## Ограничения
- Minute-rate limit пока не реализован.
- Reconnect/Last-Event-ID дедуп протокол пока не реализован (следующий инкремент).
