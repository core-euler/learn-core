# E2E Strategy (Documentation-Only)

## Цель
Сформировать e2e-ориентир до реализации, чтобы фронт и бэк изначально собирались под проверяемые пользовательские потоки.

## Test Layers
1. Smoke E2E — критический путь авторизации и первого урока.
2. Core E2E — прогресс, экзамен, консультант, лимиты.
3. Resilience E2E — реконнект стриминга, ошибки сети, устойчивость UI.

## Test Data Policy
- Выделенный тестовый контент-индекс с минимальным набором модулей/уроков.
- Предопределённые тестовые пользователи:
  - new_user (нулевой прогресс)
  - mid_user (частичный прогресс)
  - consultant_user (доступ к consultant)
- Изоляция данных между прогоном тестов обязательна.

## Candidate E2E Suites

### Suite A — Auth & Entry
- Login success (email).
- Login failure (invalid credentials).
- Redirect from private route when unauthorized.
- Telegram login callback happy path (через тестовый мок).

### Suite B — Learning Progression
- Continue from dashboard opens first available lesson.
- Complete lecture unlocks next lesson.
- Locked lesson cannot be accessed directly.
- Completing module unlocks consultant gate.

### Suite C — Exam Flow
- Start exam creates fixed question set.
- Finish exam with passing score marks lesson completed.
- Failed attempt does not unlock next lesson.

### Suite D — Consultant Scope
- Consultant unavailable before prerequisite.
- Consultant retrieval excludes locked lesson knowledge (observable by bounded response contract).

### Suite E — Streaming & Recovery
- Lecture response streams progressively.
- Reconnect does not duplicate rendered chunks/messages.
- Stream timeout/error shows recoverable state.

### Suite F — Limits
- Daily request limit produces dedicated UI state.
- Per-minute limit produces throttling state.
- Post-reset behavior recovers normal send.

## Quality Gates for MVP
- Все smoke и core e2e стабильны.
- Нет блокирующих flaky-тестов в критическом пути.
- Ошибки доступа/лимитов воспроизводимы и детерминированы.

## Non-Goals (MVP)
- Визуальная пиксель-перфект проверка.
- Нагрузочные e2e сценарии.
- Кросс-браузерная матрица beyond baseline.
