# Frontend MVP Shell

Vite + React + TypeScript frontend for LLM Handbook MVP.

## What is implemented
- Public routes: `/login`, `/register`
- Private routes with guard + redirect flow:
  - `/dashboard`
  - `/modules`
  - `/modules/:moduleId`
  - `/lessons/:lessonId/lecture`
  - `/lessons/:lessonId/exam`
  - `/lessons/:lessonId/consultant`
  - `/profile`
- Session bootstrap via `GET /api/auth/me`
- MVP app shell in ChatGPT/Claude-like pattern:
  - left sidebar = course tree (modules/lessons from `GET /api/progress`)
  - main area = active workspace/chat
- Dashboard progress + Continue CTA (`next_lesson_id`) + empty state
- Modules/lessons statuses (`locked|available|completed`)
- Locked lesson handling (`403 lesson_locked`)
- Lesson workspace and AI modes:
  - chat-first workspace (mode tabs + chat zone)
  - lesson content moved to secondary readable block
  - Lecture: JSON fallback + SSE streaming render
  - Exam: start/finish, score/pass-fail
  - Consultant: JSON-only + gate by `consultant_unlocked`
- Limits UX mapping:
  - `minute_rate_limited`
  - `daily_limit_exceeded`
- Minimal smoke tests (Vitest + RTL)

## Run
```bash
npm install
npm run dev
```

Optional API base URL:
```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Test / Build
```bash
npm test
npm run build
```
