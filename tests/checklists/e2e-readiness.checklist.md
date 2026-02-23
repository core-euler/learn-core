# E2E Readiness Checklist

## Environment
- [ ] Определено отдельное e2e-окружение.
- [ ] Есть минимальный тестовый контент-индекс.
- [ ] Есть тестовые пользователи с разным прогрессом.

## Contracts Alignment
- [ ] Frontend state maps согласованы с backend контрактами.
- [ ] Все e2e кейсы имеют ссылку на requirement/contract.
- [ ] Нет неописанных критических UI-переходов.

## Stability
- [ ] Определены ретраи только для сетевых нестабильностей.
- [ ] Для стриминга есть deterministic oracle (признак завершения).
- [ ] Для лимитов есть контролируемые тестовые значения.

## MVP Gates
- [ ] G0: `pytest -q` проходит без падений (exit code 0).
- [ ] G1: `backend/tests/test_smoke_e2e_happy_path.py::test_smoke_e2e_happy_path_auth_course_progress_ai` проходит стабильно.
- [ ] Smoke e2e сценарии определены как блокирующие (P0 hard gate).
- [ ] Core e2e сценарии определены как обязательные.
- [ ] Resilience e2e сценарии определены как рекомендованные к релизу MVP.
