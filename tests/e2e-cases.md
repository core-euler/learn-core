# E2E Cases Backlog (Given/When/Then)

## E2E-A1: Unauthorized redirect
- Given пользователь без сессии
- When открывает `/dashboard`
- Then перенаправляется на `/login`

## E2E-A2: Login success
- Given валидный пользователь email/пароль
- When отправляет форму login
- Then попадает на `/dashboard` и видит блок прогресса

## E2E-B1: Continue CTA
- Given пользователь с доступным уроком
- When нажимает `Continue`
- Then открывается первый available урок

## E2E-B2: Locked lesson blocked
- Given пользователь без доступа к уроку
- When открывает URL locked урока
- Then видит blocked/forbidden состояние и не видит контент урока

## E2E-B3: Lecture completion unlock
- Given lesson в статусе available
- When пользователь завершает урок в lecture mode
- Then урок становится completed и следующий урок становится available

## E2E-C1: Exam pass progression
- Given lesson available и exam session создана
- When пользователь завершает экзамен с проходным результатом
- Then lesson marked completed и прогресс обновляется на UI

## E2E-C2: Exam fail no unlock
- Given lesson available и exam session создана
- When результат ниже проходного
- Then lesson не переводится в completed

## E2E-D1: Consultant gate
- Given пользователь без completed модуля
- When открывает consultant mode
- Then видит состояние недоступности

## E2E-E1: Streaming no duplicate on reconnect
- Given активный поток ответа
- When происходит разрыв соединения и реконнект
- Then UI не дублирует уже полученные части ответа

## E2E-F1: Daily limit state
- Given пользователь превысил дневной лимит
- When отправляет сообщение
- Then видит лимитное состояние с указанием reset-ориентира
