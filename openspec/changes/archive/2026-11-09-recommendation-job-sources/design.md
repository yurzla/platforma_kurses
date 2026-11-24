# Design

## Backend

В `application/handlers.py` добавляется преобразование `CourseMatch` в источник:

```python
{
    "source_type": "course_recommendation",
    "course_id": match.course_id,
    "course_title": match.title,
    "course_url": f"/courses/{match.course_id}",
    "score": match.score,
}
```

В ветке `session.course_id is None and looks_like_course_query(...)`, где уже есть
`matches`, источники формируются один раз и передаются:

- в `ChatMessage(..., sources=recommendation_sources, used_chunk_ids=[])`;
- в `uow.jobs.mark_done(job_id, answer, recommendation_sources, rewritten)`.

Алгоритм `rank_courses` и `CourseMatch` не меняются. При отсутствии совпадений
ветка не входит, поэтому пустые источники остаются как раньше.

## Web

`renderJobDetail` делит `job.sources` на два набора:

- `source_type === "course_recommendation"` — рекомендации;
- остальные — чанки.

Для рекомендаций рендерится таблица «Рекомендованные курсы»: курс-ссылка и
`score`. Для чанков сохраняется текущая таблица. Сообщение «источники не
сохранены» выводится только если оба набора пусты.

## Совместимость

- Существующие job-ы с чанковыми источниками отображаются без изменений.
- `application/chat_export.py::collect_sources` уже использует `course_title` и
  `course_url`, поэтому рекомендательные источники корректно попадут в экспорт.
- JSONB `jobs.sources` и `chat_messages.sources` менять не нужно.

## Testing

- Unit: рекомендательный сценарий сохраняет два источника с нужными полями и
  дублирует их в assistant-сообщении.
- Unit: обычный чанковый сценарий не меняется.
- Web: `dashboard.js` содержит обработку `course_recommendation`.
- Integration: не требуется, схема БД не меняется.
