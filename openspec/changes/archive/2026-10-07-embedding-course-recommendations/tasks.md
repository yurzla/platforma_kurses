## 1. Domain

- [x] 1.1 `domain/recommender.py`: `CourseMatch`, `looks_like_course_query`, `select_courses`, `render_recommendations`
- [x] 1.2 `domain/prompts.py`: `build_recommendation_expansion_prompt`, публичный `CATALOG_DESCRIPTION_LIMIT`
- [x] 1.3 `domain/recommendations.py`: удалять пункт с валидной ссылкой, но кавычечным заголовком-не-курсом

## 2. Application

- [x] 2.1 `ports.py`: `CourseRecommender` + поле `recommender` в `UnitOfWork`
- [x] 2.2 `application/recommendations.py`: `rank_courses` (расширение → эмбеддинг → отбор)
- [x] 2.3 `handlers.process_question`: ветка рекомендаций для глобальных сессий, fallback на RAG

## 3. Adapters & config

- [x] 3.1 `SqlCourseRecommender` + wiring в `unit_of_work.py`
- [x] 3.2 `config.py` и `docker-compose.yml`: `recommendation_top_k/margin/min_score`
- [x] 3.3 `scripts/embed_chunks.py`: пере-эмбеддинг при изменении текста описания

## 4. Tests

- [x] 4.1 `tests/fakes.py`: `InMemoryCourseRecommender` + `FakeStore.recommendations`
- [x] 4.2 `tests/unit/test_recommender.py`: отбор, интент, рендер, rank_courses
- [x] 4.3 `tests/unit/test_handlers.py`: ветка рекомендаций, fallback, курсовая сессия
- [x] 4.4 `tests/unit/test_recommendations.py`: удаление linked-пункта с неизвестным заголовком
- [x] 4.5 `tests/integration/test_recommender.py`: ранжирование по вектору

## 5. Verification

- [x] 5.1 `make lint`, `make typecheck`, `make test`
- [x] 5.2 Пересборка контейнеров; «какие курсы по js есть?» → {3,6,9,10}, «курсы по фронтенду» → {9,10,6}
- [x] 5.3 `openspec validate embedding-course-recommendations --strict` и архивация
