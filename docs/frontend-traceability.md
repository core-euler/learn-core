# Frontend Traceability Matrix

_Last sync: 2026-02-23_

Цель: связать фронтовые требования с документацией, контрактами и проверками.

| Frontend Requirement | Source Doc Section | Contract Artifact | Verification Artifact |
|---|---|---|---|
| Private routes require active session | docs/frontend.md (Auth UX Contract) | tests/contracts/frontend.contract.md | frontend smoke: unauthorized redirect |
| Dashboard shows progress and Continue CTA | docs/frontend.md (Dashboard UX Contract) | docs/frontend-api-canonical.md (Progress/Course Contract) | tests/checklists/frontend-readiness.checklist.md |
| Locked lessons are blocked | docs/frontend.md (Modules & Lessons UX) | docs/frontend-api-canonical.md (Lesson content access) | tests/contracts/frontend.contract.md |
| Lesson workspace chat-first behavior | docs/frontend.md (Lesson Workspace Layout) | docs/frontend-state-maps.md | tests/checklists/phase-7-frontend-app.checklist.md |
| Lecture supports streaming and reconnect | docs/frontend.md (Lecture + Streaming UX) | docs/frontend-api-canonical.md (Lecture SSE Reliability Contract) | tests/contracts/streaming-limits.contract.md |
| Exam produces pass/fail and updates progress | docs/frontend.md (Exam Mode UX) | docs/frontend-api-canonical.md (Exam mode contract) | tests/contracts/frontend.contract.md |
| Consultant availability is server-gated | docs/frontend.md (Consultant Mode UX) | docs/frontend-api-canonical.md (Consultant mode contract) | tests/checklists/frontend-readiness.checklist.md |
| Limit errors are mapped into distinct UX states | docs/frontend.md (Limits & Errors UX) | docs/frontend-api-canonical.md (Limits and Error Mapping) | tests/e2e-priority-matrix.md |
| MVP release decision for frontend is explicit | docs/release-readiness.md (Test Gates) | tests/checklists/frontend-readiness.checklist.md | tests/e2e-priority-matrix.md |

## Traceability Rule
- Любое изменение frontend UX/API должно обновлять минимум один contract artifact и один verification artifact.
- Изменение без traceability-связки считается незавершённым по методике.
