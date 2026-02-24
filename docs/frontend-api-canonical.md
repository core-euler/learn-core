# Frontend API Canonical Contract (MVP)

_Last sync: 2026-02-23_

Цель документа: единый источник истины для фронтенда по API-контрактам, ошибкам, ограничениям и streaming-поведению.

## 1) Contract Rules
- Backend является единственным источником истины для доступа, прогресса и блокировок.
- Frontend не принимает решений о доступе к урокам локально без серверного подтверждения.
- Все UX-переходы опираются на серверные поля и серверные коды ошибок.
- Для chat-ответов обязательно различать JSON и SSE-режимы.

## 2) Auth/Session Contract

### Session bootstrap
- Endpoint: `GET /api/auth/me`
- Успех: профиль текущего пользователя.
- Ошибка: `401` инициирует logout-state и переход на `/login`.

### Login
- Endpoint: `POST /api/auth/login`
- Успех: сервер подтверждает вход и выставляет auth-cookie.
- Post-condition: frontend переводит пользователя на `/dashboard`.

### Logout
- Endpoint: `POST /api/auth/logout`
- Post-condition: frontend очищает клиентский state и возвращает пользователя на публичный роут.

## 3) Progress/Course Contract

### Dashboard source
- Endpoint: `GET /api/progress`
- Обязательные поля для app shell:
  - `overall_percent`
  - `next_lesson_id`
  - `consultant_unlocked`
  - `modules[].lessons[]` со статусами уроков

### Continue CTA
- Если `next_lesson_id` задан, CTA ведёт в соответствующий урок.
- Если `next_lesson_id` отсутствует, Dashboard показывает empty-state.

### Modules list
- Endpoint: `GET /api/modules`
- Назначение: список модулей и базовая мета-информация для левой колонки курса.

### Lesson content access
- Endpoint: `GET /api/lessons/{lesson_id}/content`
- Успех: урок и контент доступны.
- Ошибка доступа: `403` + `detail=lesson_locked`.

## 4) Chat Modes Contract

### Lecture mode
- Endpoint: `POST /api/chat/lecture`
- Режимы ответа:
  - JSON envelope
  - SSE stream (`chunk`/`done`)
- Frontend обязан поддерживать stream rendering и recoverable-поведение при разрывах.

### Exam mode
- Start: `POST /api/chat/exam/start`
- Finish: `POST /api/chat/exam/finish`
- Контракт результата: score/pass-fail и серверное подтверждение прогресса урока.

### Consultant mode
- Endpoint: `POST /api/chat/consultant`
- Текущий baseline: JSON-only.
- Preconditions:
  - server-side gate: `consultant_unlocked`
  - fallback guard: `403` + `detail=consultant_locked`

## 5) Retrieval Envelope Contract
- Lecture/Consultant ответы содержат retrieval-блок:
  - `top_k`
  - `chunks_found`
  - `citations[]`
- Frontend использует citations как объяснение источника ответа, не как замену основного текста.

## 6) Limits and Error Mapping
- Chat endpoints возвращают `429` с `detail`:
  - `minute_rate_limited`
  - `daily_limit_exceeded`
- Frontend обязан показывать два разных UX-состояния для этих случаев.
- Network/runtime ошибки показываются как recoverable error без потери уже полученного контента.

## 7) CSRF Contract (state-changing requests)
- Для state-changing запросов frontend отправляет CSRF header в соответствии с серверной схемой double-submit.
- Ошибка CSRF (`403 csrf_failed`) должна трактоваться как security-state и приводить к безопасному повтору через обновление сессии.

## 8) Lecture SSE Reliability Contract
- Lecture streaming использует последовательные события `chunk` и terminal `done`.
- Reconnect использует `Last-Event-ID`.
- Duplicate prevention обязателен: уже подтверждённые события не должны повторно рендериться.
- Если подтверждён terminal event, новый контент не переотправляется.

## 9) Frontend Pass/Fail Compatibility Criteria

### PASS
- Frontend корректно отрабатывает auth redirect, progress CTA, lesson locks, exam result, consultant gate.
- Lecture stream корректно рендерится и не дублирует контент после reconnect.
- `minute_rate_limited` и `daily_limit_exceeded` отображаются как разные состояния.

### FAIL
- Любой обход locked-state на клиенте без server confirmation.
- Смешение limit UX-состояний.
- Потеря целостности lecture stream (дубли или разрыв без recoverable UX).
- Использование неканоничных полей, не описанных в этом документе/контрактах.
