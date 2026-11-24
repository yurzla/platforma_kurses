## 1. Промпт и контекст

- [x] 1.1 `domain/prompts.py`: `SYSTEM_PROMPT` — grounding только по «МАТЕРИАЛЫ КУРСА» и «РЕКОМЕНДУЕМЫЕ КУРСЫ»; правило про блок «Источники» силами модели; формат ссылок без пробелов
- [x] 1.2 `domain/prompts.py`: `build_answer_system_prompt`/`build_answer_messages` — вместо `catalog` параметр `recommended_courses`; секция «МАТЕРИАЛЫ КУРСА» только при непустом контексте
- [x] 1.3 `domain/context.py`: метка фрагментов `[Источник i]`

## 2. Приложение

- [x] 2.1 `application/rag.py`: `generate_answer` — убрать `catalog`, добавить `recommended_courses`
- [x] 2.2 `domain/recommender.py`: удалить `render_recommendations`, добавить `build_recommended_courses_section`
- [x] 2.3 `application/handlers.py`: убрать построение каталога и вызовы `build_sources_section`; рекомендательная ветка — ответ модели из секции рекомендованных; нет чанков → `NO_MATERIALS_ANSWER` без LLM; sanitize — по источникам
- [x] 2.4 `config.py`: удалить `catalog_prompt_limit`

## 3. Тесты

- [x] 3.1 `tests/unit/test_domain.py`: `[Источник i]`, секция рекомендованных, промпт без каталога, блок «Источники»; удалить тесты каталога/`build_sources_section`
- [x] 3.2 `tests/unit/test_recommender.py`: `build_recommended_courses_section`
- [x] 3.3 `tests/unit/test_handlers.py`: нет LLM-ответа без чанков; рекомендательная ветка отвечает моделью; сохранение блока «Источники» из ответа модели
- [x] 3.4 `tests/api/test_api.py`: убрать детерминированные проверки секции источников

## 4. Проверка

- [x] 4.1 `make lint`, `make typecheck`, `make test`
- [x] 4.2 `openspec validate llm-authored-grounded-answers --strict`
- [x] 4.3 Ручная проверка ответов (course/global/рекомендации/нет материалов)
