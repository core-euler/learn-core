# Implementation Checklist (Execution Plan)

_Last update: 2026-02-23_

Цель: довести текущую реализацию до управляемого MVP-ready состояния без распыления.

## 0) Базовые правила исполнения
- Работать блоками по 60–120 минут.
- После каждого блока фиксировать артефакт (код/тест/дока), а не «статус». 
- Любая фича считается завершённой только при: код + тест + обновлённая документация.

---

## 1) Security Hardening (P0)

### 1.1 CSRF для state-changing endpoints
- [ ] Внедрить double-submit CSRF token схему.
- [ ] Защитить минимум: `login/refresh/logout/logout-all`, AI chat POST-endpoints, progress update endpoints (если есть POST/PATCH).
- [ ] Добавить негативные/позитивные тесты на отсутствие/невалидный/валидный CSRF.
- **DoD:** state-changing запросы без CSRF режутся стабильно, тесты зелёные.

### 1.2 Password/KDF policy для production
- [x] Зафиксировать и внедрить production policy (argon2id/scrypt + параметры).
- [x] Документировать migration strategy для существующих хешей.
- [x] Добавить тесты на верификацию старых/новых хешей (если migration-in-place).
- **DoD:** политика описана в docs + покрыта тестами + включается через env/config.

### 1.3 Test routes isolation audit
- [ ] Перепроверить, что test-only endpoints недоступны вне `APP_ENV=test`.
- [ ] Добавить smoke-тест на prod-like env.
- **DoD:** нет утечек тестовых ручек в non-test окружения.

---

## 2) Data & Infra (P0/P1)

### 2.1 Alembic migrations
- [x] Инициализировать Alembic.
- [x] Создать initial migration по текущим моделям.
- [x] Добавить команду миграций в README/операционный чеклист.
- **DoD:** чистый подъём БД через миграции в пустой Postgres (команды и smoke-check добавлены; postgres smoke запускается при `TEST_POSTGRES_DATABASE_URL`).

### 2.2 Content ingestion flow (production-safe)
- [x] Ввести индекс-контракт контента (версия, module/lesson map).
- [x] Добавить валидатор структуры контента (на старте или отдельной командой).
- [x] Добавить тест на битый/неполный контент.
- **DoD:** контент грузится предсказуемо, ошибки контента диагностируемы заранее.

### 2.3 Docker/ops polish
- [x] Проверить healthcheck для backend/postgres.
- [x] Зафиксировать `.env.example` с обязательными ключами.
- [x] Документировать локальный и staging runbook.
- [x] Добавить/обновить smoke-проверки для ops-артефактов (без ломки CI).
- **DoD:** новый разработчик поднимает стенд по README без догадок. ✅ Закрыто (2026-02-23).

---

## 3) AI Layer Maturation (P1)

### 3.1 Replace stubs with provider adapter
- [x] Ввести адаптер LLM provider (интерфейс + реализация по умолчанию).
- [x] Убрать stub-ответы в lecture/consultant/exam flows.
- [x] Добавить graceful fallback/timeout policy.
- **DoD:** backend flows переведены на adapter-контракт, fallback покрыт тестами (успех/таймаут/ошибка).

### 3.2 RAG contract (minimal)
- [ ] Определить минимальный retrieval contract (chunk metadata, top-k, citations).
- [ ] Добавить заглушку индекса + интерфейс retriever.
- [ ] Документировать ожидаемое поведение в `docs/spec.md` (без кода, на уровне контракта).
- **DoD:** архитектура RAG формализована и готова к инкрементной реализации.

### 3.3 SSE reliability
- [ ] Улучшить reconnect протокол (не только Last-Event-ID equality).
- [ ] Протестировать сценарии: reconnect, duplicate prevention, partial stream resume.
- **DoD:** поток устойчив к обрывам, поведение формализовано в тестах.

---

## 4) Frontend Enablement (P1)

### 4.1 API compatibility pass
- [ ] Сверить фактические backend response shapes с frontend-contract.
- [ ] Закрыть рассинхроны в `docs/frontend-state-maps.md` и `tests/contracts/frontend.contract.md`.
- **DoD:** фронт может интегрироваться без ad-hoc правок API «на лету».

### 4.2 Minimal app shell readiness
- [ ] Подтвердить минимальный набор экранов/состояний для MVP.
- [ ] Составить короткий список missing backend capabilities (если есть).
- **DoD:** есть чёткая граница «что уже можно собирать во фронте сегодня».

---

## 5) Quality Gates & Release (P0)

### 5.1 Test gate hardening
- [ ] Добавить smoke e2e (happy path): auth → course/progress → ai endpoint.
- [ ] Зафиксировать минимальные quality gates для релиза.
- **DoD:** release decision делается по явным критериям, а не «на глаз».

### 5.2 Documentation sync
- [ ] После каждого закрытого пункта обновлять:
  - `docs/changelog.md`
  - `docs/release-readiness.md`
  - релевантные contracts/checklists
- **DoD:** документация не отстаёт от кода.

---

## Suggested execution order (strict)
1. CSRF + test routes audit
2. Alembic migrations
3. Content ingestion contract
4. LLM adapter (replace stubs)
5. SSE reliability
6. Frontend compatibility pass
7. Final release-readiness pass

---

## Daily operating mini-checklist
- [ ] Выбран один главный технический outcome дня
- [ ] Сделан минимум один P0/P1 пункт до «зелёного DoD»
- [ ] Обновлён changelog/release-readiness
- [ ] Нет незакоммиченных критичных изменений к концу дня
