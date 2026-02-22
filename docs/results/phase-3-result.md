# Результат этапа 3

## Статус
В работе.

## Что реализовано
- Добавлены сущности Course/Progress: modules, lessons, user_lesson_progress, user_module_progress.
- Реализован bootstrap прогресса пользователя при регистрации (первый модуль/урок available).
- Реализованы endpoints:
  - `GET /api/progress`
  - `POST /api/progress/lessons/{lesson_id}/complete`
- Добавлены тесты phase-3 логики: `backend/tests/test_course_progress.py`.

## Тесты
- Общий прогон: 10 passed.

## Ограничения
- Контент/модули пока seed-ятся тестовым endpoint-ом `_test/seed-course`.
- Полные production endpoints modules/lessons ещё в следующем инкременте.
