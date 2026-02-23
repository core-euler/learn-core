# Frontend Specification (MVP)

## 1) Scope
Документ описывает только фронтенд-поведение и UX-контракты, согласованные с backend-документацией.

## 2) Routing Model
- Public:
  - `/login`
  - `/register`
- Private:
  - `/dashboard`
  - `/modules`
  - `/modules/:moduleId`
  - `/lessons/:lessonId`
  - `/lessons/:lessonId/lecture`
  - `/lessons/:lessonId/exam`
  - `/lessons/:lessonId/consultant`
  - `/profile`

## 3) Global UI States
Для каждого экрана и крупного блока обязательны состояния:
- Loading
- Ready
- Empty
- Error (recoverable)
- Forbidden/Locked (если доступ запрещён правилами прогресса)

## 4) Auth UX Contract (sync with phase-2)
- После успешного входа пользователь попадает на `/dashboard`.
- При 401 на защищённом роуте пользователь переводится на `/login`.
- Сообщения ошибок авторизации не раскрывают чувствительные детали проверки.
- Logout завершает текущую сессию и очищает клиентское состояние.

## 5) Dashboard UX Contract
- Показывает общий прогресс и CTA “Продолжить”.
- CTA ведёт к первому доступному уроку.
- Источник для CTA: `GET /api/progress -> next_lesson_id` (если `null`, перейти в empty-state).
- Если доступных уроков нет, показывается нейтральный empty-state с подсказкой действия.

## 6) Modules & Lessons UX Contract (sync with phase-3)
- Список модулей и уроков отображает статус: locked / available / completed.
- Locked-элементы визуально и функционально недоступны.
- Попытка открытия locked-урока показывает состояние blocked и пояснение.
- После завершения урока UI обновляет статус и разблокировки через серверный ответ.

## 7) Lesson Workspace Layout
- Desktop: 2 колонки (материал слева, чат справа).
- Mobile: переключаемые вкладки “Материал” и “Чат”.
- В шапке: прогресс текущего модуля (завершено X из Y).

## 8) Lecture Mode UX (sync with phase-4)
- При первом входе в режим отображается вводный ответ AI.
- Пользователь отправляет сообщения в пределах лимита длины.
- Ответы приходят потоково, рендерятся инкрементально.
- Кнопка “Завершить урок” доступна только если урок не completed.

## 9) Exam Mode UX
- Старт режима создаёт экзаменационную сессию.
- Вопросы фиксируются на время сессии.
- После завершения показываются: итоговый процент, pass/fail, комментарии.
- При pass UI обновляет статус урока и возможные разблокировки.

## 10) Consultant Mode UX
- Режим доступен только после завершения минимум одного модуля.
- Предикат доступности для app shell: `GET /api/progress -> consultant_unlocked`.
- При недоступности отображается объяснение условия доступа.
- В текущем backend consultant работает в JSON request/response (без SSE).
- Ответы используют retrieval envelope (`retrieval.citations[]`) и поле `source`.

## 11) Streaming & Reconnect UX (sync with phase-5)
- Поток (SSE) применяется для Lecture mode.
- Поток рендерится без дублирования сообщений при реконнекте.
- Во время потока доступен индикатор генерации.
- Ошибки потока показываются как recoverable с действием “Повторить”.

## 12) Limits & Errors UX
- При превышении лимитов показывается отдельный тип сообщения с указанием условия сброса (по backend-коду `detail`).
- `detail=daily_limit_exceeded` и `detail=minute_rate_limited` маппятся в разные UX-состояния.
- Ошибки сети отображаются без потери уже полученного контента.
- Клиент различает ошибки валидации, доступа, лимитов и временных сбоев.

## 13) Client Data Layer Contract
- Клиент не хранит критичные правила доступа локально как источник истины.
- Кэш прогресса и модулей инвалидируется после событий completion/pass.
- Идемпотентность отправки пользовательских сообщений поддерживается клиентским message-id.

## 14) Accessibility & Visual Constraints
- Фокус-стейты видимы для интерактивных элементов.
- Контраст и читаемость достаточны для тёмной темы по умолчанию.
- Основные действия доступны с клавиатуры.

## 15) Executable Readiness Checklist (MVP app shell)
- [x] Auth shell: `/login`, `/register`, redirect на `/dashboard` после login.
- [x] Route guard: `401` на private data ведёт к logout+redirect `/login`.
- [x] Dashboard ready-state: `overall_percent` отрисовывается из `/api/progress`.
- [x] Continue CTA: берёт `next_lesson_id` из `/api/progress`.
- [x] Empty dashboard: при `next_lesson_id=null` показывается нейтральный empty-state.
- [x] Modules list: статусы `locked|available|completed` на основе `/api/progress`.
- [x] Lesson locked state: `GET /api/lessons/{id}/content -> 403 lesson_locked`.
- [x] Lecture state machine: JSON + SSE (`chunk/done`) с reconnect без дублей.
- [x] Exam shell: start/finish + score/pass/fail.
- [x] Consultant gate: `consultant_unlocked` из `/api/progress` + `403 consultant_locked` как fallback-guard.
- [x] Error mapping: `429 minute_rate_limited|daily_limit_exceeded` в отдельные UX-состояния.

## 16) Out of Scope (frontend)
- Админ-интерфейсы.
- Платёжные экраны.
- Мультиязычность.
- Продвинутые пользовательские настройки профиля.
