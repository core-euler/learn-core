# Contract: AI Modes & RAG (R7-R10)

## Scenarios
1. Lecture mode answers from current lesson context only.
2. Exam mode generates fixed question set per session.
3. Exam scoring uses criteria bound to the same session.
4. Consultant mode excludes locked lessons from retrieval scope.
5. Injection-like content in indexed material is sanitized by policy.
6. User prompt is treated as user-turn input and not escalated to system context.
7. Out-of-scope question returns bounded answer contract.

## Evidence Requirements
- Для каждого режима определяется допустимый набор источников контекста.
- Для каждого отказа определён понятный и повторяемый формат ответа.

## Release Gate Link
- Входит в блокирующий smoke-кейс `E2E-SMOKE-API-1` (успешный `POST /api/chat/lecture` с `fallback_reason=ok`).
