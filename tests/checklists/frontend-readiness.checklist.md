# Frontend Readiness Checklist (MVP, Executable)

_Last sync: 2026-02-23_

## A. Routing and Session
- [ ] Public/private route split работает стабильно.
- [ ] Неавторизованный доступ к private routes приводит к переходу на `/login`.
- [ ] После login происходит redirect на `/dashboard`.
- [ ] Logout очищает клиентский state и завершает сессию.

## B. Dashboard and Course Navigation
- [ ] Dashboard отображает `overall_percent` из server progress.
- [ ] Continue CTA использует `next_lesson_id`.
- [ ] Empty-state показывается при `next_lesson_id = null`.
- [ ] Левая колонка курса показывает server statuses (`locked|available|completed`).

## C. Lesson Access and Progress Rules
- [ ] Locked lesson корректно отображается как blocked/forbidden (`detail=lesson_locked`).
- [ ] Завершение урока обновляет progression с серверным подтверждением.
- [ ] Разблокировка следующего урока отражается после server refresh.

## D. AI Modes
- [ ] Lecture mode работает в JSON и SSE baseline.
- [ ] Lecture stream отображает chunk-by-chunk без дублирования.
- [ ] Exam mode поддерживает start/finish + итог pass/fail.
- [ ] Consultant mode доступен только при `consultant_unlocked=true`.
- [ ] Consultant locked-state отрабатывается через `detail=consultant_locked`.

## E. Limits and Errors
- [ ] `minute_rate_limited` отображается как отдельный UX-state.
- [ ] `daily_limit_exceeded` отображается как отдельный UX-state.
- [ ] Recoverable network/runtime errors не ломают уже отрисованный контент.

## F. Release Gate (Frontend)
- [ ] Frontend lint pass.
- [ ] Frontend unit/smoke tests pass.
- [ ] Frontend build pass.
- [ ] Frontend contracts и state maps синхронизированы с backend baseline.

## Pass/Fail Rule
- PASS: все блоки A–F закрыты, без критичных обходов security/progress инвариантов.
- FAIL: любой незакрытый пункт в A–D или несоответствие каноническому API-контракту.
