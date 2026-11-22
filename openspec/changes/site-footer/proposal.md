# Proposal

## Why

У страниц интерфейса нет футера: пользователь не видит, что это учебный проект, и на странице
отсутствует название проекта с логотипом за пределами верхнего меню.

## What Changes

- На всех страницах веб-интерфейса появляется общий футер.
- В футере: название проекта «Courses Assistant» с тем же логотипом (robot), что и в header,
  пометка «Учебный проект, созданный в рамках прохождения курса» и текущий год.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `web-interface`: добавлено требование к общему футеру сайта.

## Impact

- Web-шаблоны: `web/src/courses_web/templates/base.html`.
- Шаблонное окружение: `web/src/courses_web/templating.py` (глобал `current_year`).
- Стили: `web/src/courses_web/static/web.css`.
- Тесты: `tests/web/test_web.py`.
- Внешние контракты не меняются.
