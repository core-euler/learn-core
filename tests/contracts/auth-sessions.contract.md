# Contract: Auth & Sessions (R1-R3)

## Scope
Только документационный контракт для будущих автотестов.

## Scenarios
1. Telegram login accepted when payload integrity and freshness are valid.
2. Telegram login rejected when integrity check fails.
3. Telegram login rejected when payload is stale.
4. Email registration accepted with valid credentials.
5. Email login rejected with invalid credentials.
6. Refresh rotates session token and invalidates previous token.
7. Reuse of invalidated refresh token triggers global session invalidation.
8. Logout invalidates current session only.
9. Logout-all invalidates all active sessions.

## Expected Outcomes
- Результаты и ошибки однозначно определены на уровне API-контрактов.
- Поведение сессий воспроизводимо и проверяемо.
