# Frontend State Maps (E2E-Oriented)

Документ фиксирует конечные состояния UI и переходы между ними так, чтобы на их основе можно было строить e2e-сценарии.

## Обозначения
- State: текущее состояние экрана/блока.
- Trigger: событие пользователя или системы.
- Dependency: backend-контракт или внутреннее условие.
- Next: следующее состояние.

---

## 1) Auth: Login/Register

| State | Trigger | Dependency | Next |
|---|---|---|---|
| LoginIdle | Submit credentials | Auth contract (R1-R3) | LoginSubmitting |
| LoginSubmitting | Auth success | Session cookie issued | LoginSuccessRedirect |
| LoginSubmitting | Auth failure | 401/validation error | LoginError |
| LoginError | User retries | Valid input | LoginSubmitting |
| RegisterIdle | Submit registration | Auth contract | RegisterSubmitting |
| RegisterSubmitting | Registration success | User created | LoginIdle |
| RegisterSubmitting | Validation failure | Invalid payload | RegisterError |

---

## 2) Dashboard

| State | Trigger | Dependency | Next |
|---|---|---|---|
| DashboardLoading | Initial load | `/api/progress` + modules summary | DashboardReady |
| DashboardLoading | API failure | Network/server error | DashboardError |
| DashboardReady | Click Continue | First available lesson exists | LessonRouteTransition |
| DashboardReady | No available lessons | Progress domain state | DashboardEmpty |
| DashboardError | Retry | API recovers | DashboardLoading |

---

## 3) Modules & Lessons List

| State | Trigger | Dependency | Next |
|---|---|---|---|
| ModulesLoading | Initial load | Published modules API | ModulesReady |
| ModulesReady | Click available lesson | Progress allows access | LessonLoading |
| ModulesReady | Click locked lesson | Progress denies access | LessonLockedNotice |
| LessonLockedNotice | Close notice | UI action | ModulesReady |
| ModulesLoading | API failure | Transport/server error | ModulesError |
| ModulesError | Retry | API recovers | ModulesLoading |

---

## 4) Lesson Workspace (Shared)

| State | Trigger | Dependency | Next |
|---|---|---|---|
| LessonLoading | Open lesson route | Lesson metadata/content access | LessonReady |
| LessonLoading | Access denied | 403 lesson_locked | LessonForbidden |
| LessonReady | Switch mode | Mode availability rule | ModeLoading |
| LessonForbidden | Back to module | UI action | ModulesReady |

---

## 5) Lecture Mode

| State | Trigger | Dependency | Next |
|---|---|---|---|
| LectureInit | Open lecture mode | Lecture chat init contract | LectureStreamingIntro |
| LectureStreamingIntro | Stream done | SSE done event | LectureIdle |
| LectureIdle | Send message | Message length + quota | LectureStreamingReply |
| LectureStreamingReply | Stream error | SSE transport/runtime error | LectureRecoverableError |
| LectureRecoverableError | Retry send | Reconnect logic | LectureStreamingReply |
| LectureIdle | Complete lesson | Completion API | LessonCompletedToast |
| LessonCompletedToast | Sync progression | Progress refresh | LectureIdle |

---

## 6) Exam Mode

| State | Trigger | Dependency | Next |
|---|---|---|---|
| ExamInit | Start exam | Exam session creation | ExamQuestionFlow |
| ExamQuestionFlow | Submit answers | Exam answer contract | ExamEvaluating |
| ExamEvaluating | Score returned >= threshold | Exam finish contract | ExamPassed |
| ExamEvaluating | Score returned < threshold | Exam finish contract | ExamFailed |
| ExamPassed | Refresh progress | Progress contract | ExamResultReady |
| ExamFailed | Retry exam | New attempt policy | ExamInit |

---

## 7) Consultant Mode

| State | Trigger | Dependency | Next |
|---|---|---|---|
| ConsultantGateCheck | Open consultant mode | Completed module prerequisite | ConsultantReady |
| ConsultantGateCheck | Prerequisite unmet | Progress contract | ConsultantForbidden |
| ConsultantReady | Send message | Consultant chat contract (JSON response) | ConsultantRequesting |
| ConsultantRequesting | Response received | 200 + consultant payload | ConsultantReady |
| ConsultantRequesting | Error | 4xx/5xx transport/runtime | ConsultantRecoverableError |

---

## 8) Limits & Rate Errors (Cross-Mode)

| State | Trigger | Dependency | Next |
|---|---|---|---|
| AnyChatIdle | Send message over daily quota | 429 `detail=daily_limit_exceeded` | DailyLimitState |
| AnyChatIdle | Send message over minute rate | 429 `detail=minute_rate_limited` | MinuteRateLimitState |
| DailyLimitState | Time passes to reset | Backend reset time reached | AnyChatIdle |
| MinuteRateLimitState | Cooldown passes | Throttle window elapsed | AnyChatIdle |

---

## 9) Reconnect / Dedup (Cross-Mode Streaming)

| State | Trigger | Dependency | Next |
|---|---|---|---|
| StreamingActive | Network drop | Client reconnect policy | Reconnecting |
| Reconnecting | Reconnect success | Last event reference honored | StreamingActiveNoDup |
| Reconnecting | Reconnect fail | Timeout policy | StreamingRecoverableError |
| StreamingRecoverableError | User retries | Transport restored | StreamingActive |
