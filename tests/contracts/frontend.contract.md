# Contract: Frontend App Behavior (sync with backend contracts)

## Scenarios
1. Unauthorized user on private route is redirected to login.
2. Dashboard “Continue” routes to first available lesson.
3. Locked lesson cannot be opened and shows blocked state.
4. Lesson completion updates UI statuses using server-confirmed state.
5. Lecture stream renders incrementally and survives reconnect without duplicates.
6. Exam finish renders score/pass-fail and updates progression view.
7. Consultant mode is unavailable before module completion.
8. Limit errors are rendered as dedicated UX state with reset hint.

## Validation Targets
- Frontend state transitions are deterministic.
- Frontend does not bypass backend authorization/progress rules.
- Streaming UX remains coherent under transient network failures.
