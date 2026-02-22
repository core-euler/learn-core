# Результат этапа 3

## Статус
В работе.

## Что реализовано
- Добавлены сущности Course/Progress: modules, lessons, user_lesson_progress, user_module_progress.
- Реализован bootstrap прогресса пользователя при регистрации (первый модуль/урок available).
- Реализованы endpoints:
  - `GET /api/progress`
  - `POST /api/progress/lessons/{lesson_id}/complete`
  - `GET /api/modules`
  - `GET /api/modules/{module_id}`
  - `GET /api/lessons/{lesson_id}`
  - `GET /api/lessons/{lesson_id}/content` (с lock-проверкой)
- Добавлены тесты phase-3 логики:
  - `backend/tests/test_course_progress.py`
  - `backend/tests/test_course_content.py`

## Тесты
- Общий прогон: 13 passed.

## Ограничения
- Контент/модули пока seed-ятся тестовым endpoint-ом `_test/seed-course`.
- `GET /api/progress` доведён до вложенной структуры modules/lessons.
- `GET /api/progress/stats` реализован с базовым usage stub (`total_ai_requests=0`, `requests_today=0`).
