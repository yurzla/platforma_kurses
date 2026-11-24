## 1. Тема

- [x] 1.1 Светлая палитра и статусные переменные в `dashboard.css` — проверка: визуальная проверка обеих тем
- [x] 1.2 `static/theme.js` (init, toggle, `localStorage`, системная тема) — проверка: переключение и сохранение после перезагрузки
- [x] 1.3 No-flash inline-скрипт и кнопка темы в `base.html`/`dashboard.html`/`login.html` — проверка: тема применяется без мигания на дашборде и логине

## 2. Верификация

- [x] 2.1 Тесты: `/static/theme.js` и `dashboard.css` отдаются, кнопка темы есть в разметке — проверка: `tests/api/test_admin.py`
- [x] 2.2 `ruff`, `mypy`, `pytest -m "not integration"` — проверка: зелёные
