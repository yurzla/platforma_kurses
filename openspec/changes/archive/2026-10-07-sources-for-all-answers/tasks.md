## 1. Источники во всех ответах

- [x] 1.1 `domain/prompts.py`: `build_sources_section(courses, *, answer=None)` — все курсы при `answer=None`, только упомянутые при `answer`; дедуп; убрать `always_ids`/импорт `Collection`
- [x] 1.2 `application/handlers.py`: RAG-ветка — секция со всеми `source_courses`; ветка ответа по каталогу — секция из упомянутых `catalog_links`; убрать `CATALOG_DESCRIPTION_LIMIT` из импортов
- [x] 1.3 `application/handlers.py`: рекомендательная ветка — секция из рекомендованных курсов
- [x] 1.4 `tests/unit/test_domain.py`: обновить тесты `build_sources_section`
- [x] 1.5 `tests/unit/test_handlers.py`: переписать проверки источников (все источники, каталог-онли, рекомендации)

## 2. Формат списка рекомендаций

- [x] 2.1 `config.py`: `recommendation_description_limit: int = 120`
- [x] 2.2 `docker-compose.yml`: env `RECOMMENDATION_DESCRIPTION_LIMIT`
- [x] 2.3 `domain/recommender.py`: `render_recommendations` — пункты через пустую строку
- [x] 2.4 `application/handlers.py`: передавать `recommendation_description_limit`
- [x] 2.5 `tests/unit/test_recommender.py`: обновить ожидаемый вывод

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate sources-for-all-answers --strict`
- [x] 3.3 Ручная проверка ответов (RAG/рекомендации/каталог/нет материалов)
