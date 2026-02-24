# Contract: Frontend App Behavior (sync with backend contracts)

## Scenarios
1. Unauthorized user on private route is redirected to login.
2. Dashboard “Continue” routes to `next_lesson_id` from backend progress envelope.
3. Locked lesson cannot be opened and shows blocked state.
4. Lesson completion updates UI statuses using server-confirmed state.
5. Lecture stream renders incrementally and survives reconnect without duplicates.
6. Exam finish renders score/pass-fail and updates progression view.
7. Consultant mode is unavailable before module completion.
8. Limit errors are rendered as dedicated UX state with reset policy hint (by error code mapping).

## Validation Targets
- Frontend state transitions are deterministic.
- Frontend does not bypass backend authorization/progress rules.
- Streaming UX remains coherent under transient network failures.
- Frontend behavior is fully aligned with `docs/frontend-api-canonical.md` and `docs/frontend-state-maps.md`.

## API Response Shapes used by frontend (4.1 compatibility baseline)

### Auth
- `POST /api/auth/login` → `200 {"ok": true}` + cookies: `access_token`, `refresh_token`, `csrf_token`
- `GET /api/auth/me` → `200 {"id": str, "email": str|null, "first_name": str, "auth_method": "email"|"telegram"}`

### Dashboard / Progress
- `GET /api/progress` →
  - `overall_percent: int`
  - `next_lesson_id: str|null` (server-computed CTA target for Dashboard Continue)
  - `consultant_unlocked: bool` (server-computed consultant availability predicate)
  - `modules: [{ module_id, status, completed_at|null, lessons: [{ lesson_id, status, exam_score|null, exam_attempts, completed_at|null }] }]`
- `GET /api/modules` → `{ modules: [{ id, title, description|null, order_index, lessons_count }] }`

### Lesson content / locking
- `GET /api/lessons/{id}/content`:
  - `200 { lesson_id, title, content }`
  - `403 { detail: "lesson_locked" }`

### Lecture chat
- `POST /api/chat/lecture` (JSON mode) →
  - `{ session_id, reply, provider, fallback_used, fallback_reason, retrieval: { top_k, chunks_found, citations[] } }`
- `POST /api/chat/lecture` (`Accept: text/event-stream`) → SSE events:
  - `chunk` and `done`
  - `id` format `<message_id>:<seq>`
  - reconnect via `Last-Event-ID` with duplicate prevention

### Exam
- `POST /api/chat/exam/start` → `{ session_id, questions[], provider, fallback_reason }`
- `POST /api/chat/exam/finish` → `{ session_id, score, passed, lesson_completed, answers[] }`

### Consultant
- `POST /api/chat/consultant` → JSON (non-SSE in current backend):
  - `{ session_id, reply, source, provider, fallback_used, fallback_reason, retrieval: { top_k, chunks_found, citations[] } }`

### Limits / errors
- Chat endpoints return `429 { detail: "minute_rate_limited" | "daily_limit_exceeded" }`.
- Frontend maps `detail` to dedicated UX states and reset hints.
