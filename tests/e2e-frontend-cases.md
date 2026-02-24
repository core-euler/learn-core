# E2E Frontend Cases + Priority Matrix

_Last sync: 2026-02-24_

## Source of truth
- Cases baseline: `tests/e2e-cases.md`
- Priority matrix baseline: `tests/e2e-priority-matrix.md`

## P0 (release blockers)
- Auth happy path and private-route redirect.
- Dashboard load with valid progress envelope.
- Continue CTA uses `next_lesson_id`.
- Locked lesson access returns blocked UX.
- Lecture stream renders chunk-by-chunk and reconnects without duplicates.

## P1
- Exam start/finish with pass/fail UI mapping.
- Consultant gate (`consultant_unlocked`) and locked-state UX.
- Limit error split: `minute_rate_limited` vs `daily_limit_exceeded`.

## P2
- Secondary navigation and empty-state variants.
- Extended reconnect edge cases and long-idle recovery.

## Rule
При конфликте между этим файлом и базовыми e2e-документами приоритет за `tests/e2e-cases.md` + `tests/e2e-priority-matrix.md`; этот файл должен быть сразу синхронизирован.
