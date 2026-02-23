# LLM Handbook — Спецификация проекта

## Обзор
LLM Handbook — образовательная платформа с контентом в Markdown и AI-ментором на базе RAG.
Пользователь проходит курс по модулям и урокам в трёх режимах: Лекция, Экзамен, Консультант.

## Функциональные требования
- R1. Платформа поддерживает два способа входа: Telegram и email/пароль.
- R2. Для Telegram-входа выполняются проверки целостности, свежести и валидности источника.
- R3. Сессии пользователя реализуются через access/refresh модель с ротацией refresh-токена.
- R4. Прогресс обучения хранится по урокам и модулям с состояниями locked/available/completed.
- R5. Следующий урок открывается только после завершения предыдущего.
- R6. Следующий модуль открывается только после завершения всех уроков текущего.
- R7. В режиме Лекция AI работает только по материалу текущего урока.
- R8. В режиме Экзамен AI формирует набор вопросов и оценивает ответы по фиксированным критериям сессии.
- R9. В режиме Консультант AI использует только открытые пользователю материалы.
- R10. Все AI-режимы используют защиту от prompt injection на этапе индексации, сборки контекста и пользовательского ввода.
- R11. Все чат-режимы поддерживают потоковую отдачу ответа и устойчивое восстановление при переподключении.
- R12. Платформа применяет дневные и минутные лимиты на запросы.

## Нефункциональные требования
- N1. MVP не включает платежи, админ-панель, мобильное приложение и мультиязычность.
- N2. Архитектура должна быть контейнеризуемой и воспроизводимой.
- N3. Доступ к контенту проверяется на сервере, а не только в интерфейсе.
- N4. Компонент векторного поиска изолируется внутренним интерфейсом для замены реализации в будущем.
- N5. Документация остаётся единственным актуальным источником требований.

## Архитектура (логическая)
- Frontend-приложение для авторизации, навигации по курсу, отображения прогресса и AI-диалогов.
- Backend API для авторизации, сессий, прогресса, доступа к контенту и AI-оркестрации.
- Реляционная база данных для пользователей, прогресса, сессий и истории сообщений.
- Векторное хранилище для чанков учебного контента и семантического поиска.
- Хранилище исходных Markdown-материалов курса.
- LLM-провайдер для генерации ответов в трёх режимах.

## Контракт LLM Provider Adapter
AI-оркестрация backend работает через внутренний provider adapter контракт (без привязки к конкретному внешнему вендору).

Минимальные операции контракта:
- `lecture_reply(lesson_id, message, message_id) -> {text, tokens_used, provider}`
- `consultant_reply(message, message_id) -> {text, tokens_used, provider}`
- `build_exam(lesson_id) -> {questions[], provider}`

Требования к runtime-политике:
- Вызовы lecture/consultant выполняются с timeout policy (`LLM_TIMEOUT_SECONDS`).
- При timeout/ошибке обязателен graceful fallback-ответ без 5xx для пользователя.
- В exam/start при ошибке провайдера используется fallback на default exam builder.
- API-ответы возвращают признак fallback (`fallback_used`/`fallback_reason`) для наблюдаемости и UI-state.

## Минимальный RAG retrieval contract

Для AI-режимов вводится минимальный внутренний retrieval-контракт, независимый от конкретной реализации индекса.

Вход retrieval-запроса:
- `user_id`: идентификатор пользователя (для будущих ACL/personalization политик).
- `mode`: `lecture | consultant | exam`.
- `lesson_id?`: обязателен для lesson-scoped режимов (`lecture`, `exam`), опционален для `consultant`.
- `message`: пользовательский текст запроса.
- `top_k`: верхняя граница числа возвращаемых чанков (`k > 0`).

Контракт retrieval-результата:
- `chunks[]`: список найденных чанков (не более `top_k`).
  - `metadata`: `{chunk_id, module_id, lesson_id, source_path, start_char, end_char}`.
  - `text`: текст чанка (или excerpt).
  - `score`: релевантность (float, чем выше — тем релевантнее).
- `citations[]`: нормализованные ссылки для UI/API.
  - минимум: `{chunk_id, lesson_id, source_path, quote}`.

Минимальные инварианты:
- `len(chunks) <= top_k`.
- Для `lecture`/`exam` retrieval ограничен текущим `lesson_id`.
- `citations` строятся из фактически возвращённых `chunks`.
- Пустой результат допустим (`chunks=[]`, `citations=[]`) и не является ошибкой.

Интеграция в AI flow (контрактный уровень):
- Перед генерацией ответа backend вызывает retriever и получает retrieval-result.
- API-ответ lecture/consultant содержит блок `retrieval`:
  - `top_k`,
  - `chunks_found`,
  - `citations[]`.
- Текущая реализация допускает stub-индекс/stub-retriever; контракт сохраняется неизменным при последующей замене на production retrieval.

## Контракт контент-индекса (ingestion)
Для production-safe загрузки контента используется единый индекс-файл `backend/content/index.json`.

Обязательные поля контракта:
- `version`: версия индекса (строка, semver/date-based допустимы).
- `modules[]`: упорядоченный список модулей.
  - `slug`, `title`, `order_index`.
  - `lessons[]`: упорядоченный список уроков модуля.
    - `slug`, `title`, `order_index`, `md_file_path`.

Инварианты:
- В индексе минимум один модуль и минимум один урок в каждом модуле.
- `order_index` уникален в пределах соответствующего уровня (модули, уроки в модуле).
- `slug` уникален в пределах соответствующего уровня (модули, уроки в модуле).
- `md_file_path` указывает на существующий markdown-файл под префиксом `content/`.

Валидация выполняется fail-fast (на старте backend при включённом флаге) и может запускаться отдельной командой в CI.

## SSE reconnect/reliability contract (R11)

Для `POST /api/chat/lecture` в режиме `Accept: text/event-stream` фиксируется следующий контракт восстановления потока.

Формат событий:
- Каждое SSE-событие содержит `id`, `event`, `data`.
- `event` ∈ `{chunk, done}`.
- `id` формата `<message_id>:<seq>`.
  - `seq` начинается с `1` для первого `chunk`.
  - terminal `done` имеет `seq = chunks_count + 1`.
- В `data` дублируются `type`, `sequence`, `event_id`, `message_id` (и `content` для chunk, `tokens_used` для done).

Reconnect/Resume поведение:
- Клиент передаёт `Last-Event-ID`.
- Если `Last-Event-ID` соответствует `<message_id>:<seq>`, сервер считает подтверждёнными все события `<= seq` и отправляет только события с `sequence > seq`.
- Legacy-совместимость: `Last-Event-ID == <message_id>` трактуется как «все chunk подтверждены» (replay только `done`).
- Если `Last-Event-ID` отсутствует/невалиден/относится к другому `message_id`, поток начинается с первого chunk.

Duplicate prevention инварианты:
- При корректном `Last-Event-ID` сервер не переотправляет уже подтверждённые `chunk` события.
- Если подтверждён `done` (`Last-Event-ID == <message_id>:<done_seq>`), сервер не отправляет новых событий (пустой stream-body).
- Повторные reconnect-запросы с одним и тем же `Last-Event-ID` идемпотентны по payload событий.

## Карта модулей
| Модуль | Документация | Описание |
|---|---|---|
| Foundation | docs/phases/phase-1-foundation.md | Границы MVP, словарь домена, структура документации |
| Auth & Sessions | docs/phases/phase-2-auth-sessions.md | Telegram/email вход, сессии, безопасность |
| Course & Progress | docs/phases/phase-3-course-progress.md | Модули, уроки, правила открытия и завершения |
| AI Modes & RAG | docs/phases/phase-4-ai-rag.md | Лекция/Экзамен/Консультант, retrieval и guardrails |
| Streaming & Limits | docs/phases/phase-5-streaming-limits.md | Потоковые ответы, надёжность и лимиты |
| Deploy & Operations | docs/phases/phase-6-deploy-ops.md | Инициализация контента, окружение и деплой-критерии |
| Frontend App | docs/phases/phase-7-frontend-app.md | UX-контракты, экраны и состояния интерфейса, согласованные с backend |

## Этапы реализации
- Этап 1: Foundation Documentation Pack.
- Этап 2: Auth & Session Documentation Pack.
- Этап 3: Course/Progress Documentation Pack.
- Этап 4: AI/RAG Documentation Pack.
- Этап 5: Streaming/Limits Documentation Pack.
- Этап 6: Deploy/Operations Documentation Pack.
- Этап 7: Frontend App Documentation Pack.

## Режим разработки
Проект стартует в Incremental Mode: документация и тестовые контракты наращиваются этапно, без реализации до отдельного подтверждения.

## Версия
- Версия: 0.1-docs
- Обновлено: 2026-02-22
