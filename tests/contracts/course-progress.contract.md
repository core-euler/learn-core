# Contract: Course & Progress (R4-R6)

## Scenarios
1. New user gets first lesson as available and others locked.
2. Completing lesson unlocks next lesson in module.
3. Completing all lessons unlocks next module.
4. Lesson completion via lecture action sets completed status.
5. Lesson completion via exam pass threshold sets completed status.
6. Attempt to complete locked lesson returns access denied contract.

## Invariants
- Нельзя иметь available в модуле, если предыдущий модуль не завершён.
- Нельзя завершить неразблокированный урок.

## Release Gate Link
- Входит в блокирующий smoke-кейс `E2E-SMOKE-API-1` (`next_lesson_id` доступен, completion повышает `overall_percent`).
