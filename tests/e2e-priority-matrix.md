# E2E Priority Matrix (MVP Release Gate)

## Priority Definitions
- **P0 (Blocker):** без прохождения релиз MVP запрещён.
- **P1 (Critical):** должен быть зелёным для релиза в закрытый тест; допускается временный waiver только с явным риском.
- **P2 (Important):** желателен к релизу; может быть перенесён при ограничениях.

## Cases Mapping

| Case ID | Scenario | Priority | Release Gate Rule | Rationale |
|---|---|---|---|---|
| E2E-A1 | Unauthorized redirect | P0 | Mandatory pass | Базовая защита приватных маршрутов |
| E2E-A2 | Login success | P0 | Mandatory pass | Вход в продукт — критический путь |
| E2E-B1 | Continue CTA to first available lesson | P0 | Mandatory pass | Основной пользовательский сценарий старта обучения |
| E2E-B2 | Locked lesson blocked | P0 | Mandatory pass | Недопущение обхода прогресса |
| E2E-B3 | Lecture completion unlocks next lesson | P0 | Mandatory pass | Ключевая бизнес-логика progression |
| E2E-C1 | Exam pass progression | P1 | Required for closed beta | Альтернативный путь completion |
| E2E-C2 | Exam fail does not unlock | P1 | Required for closed beta | Целостность правил прогресса |
| E2E-D1 | Consultant gate by module completion | P1 | Required for closed beta | Ограничение доступа к advanced mode |
| E2E-E1 | Streaming reconnect without duplicates | P1 | Required for closed beta | Надёжность UX в нестабильной сети |
| E2E-F1 | Daily limit state rendering | P2 | Target for MVP, waiver allowed | UX-качество лимитов, не блокирует базовый путь |
| E2E-SMOKE-API-1 | Backend happy path (auth → course/progress → ai) | P0 | Mandatory pass (hard gate) | Минимальный сквозной релизный сценарий backend |

## Gate Policy

### MVP Hard Gate (must pass)
- Все **P0** кейсы.

### Closed Beta Gate (target)
- Все **P0 + P1** кейсы.
- Допустим максимум 1 waiver по P1 при наличии:
  - документированного риска,
  - компенсирующего контроля,
  - фиксированного срока устранения.

### Post-MVP Improvement
- **P2** кейсы доводятся до зелёного статуса до расширения аудитории.

## Reporting Format
Для каждого прогона формируется таблица:

| Case ID | Priority | Status (Pass/Fail/Skipped) | Build/Commit | Notes |
|---|---|---|---|---|

## Ownership
- Product owner утверждает waiver.
- Tech lead подтверждает технический риск и mitigation.
- QA/LLM-operator фиксирует воспроизводимость фейла.
