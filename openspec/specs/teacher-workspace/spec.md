# teacher-workspace Specification

## Purpose
Рабочее пространство преподавателя: управление собственными курсами и их структурой, просмотр прогресса студентов и постраничный поиск по своим курсам.

## Requirements

### Requirement: Teacher course list

The teacher course list endpoint SHALL return only the authenticated teacher's courses with their lesson, step, and student counts, SHALL support an optional case-insensitive `search` over the title and description, and SHALL return a paginated `{items,total,limit,offset}` response controlled by `limit` (1..200) and `offset`.

#### Scenario: Own courses returned

- **WHEN** an authenticated teacher requests the teacher course list
- **THEN** the response contains only courses owned by that teacher with their counters

#### Scenario: Paginated response

- **WHEN** the teacher requests the list with `limit` and `offset`
- **THEN** `items` contains at most `limit` courses starting from `offset` and `total` reports all owned courses

#### Scenario: Search by title or description

- **WHEN** the teacher requests the list with `search`
- **THEN** only owned courses whose title or description contains the term in any case are returned and `total` counts those matches

#### Scenario: Non-teacher access denied

- **WHEN** a student requests the teacher course list
- **THEN** the system responds with HTTP 403
