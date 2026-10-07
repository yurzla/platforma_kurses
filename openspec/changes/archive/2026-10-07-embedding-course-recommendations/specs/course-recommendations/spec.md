## Purpose

Подбор курсов платформы по смыслу запроса с использованием векторных представлений (эмбеддингов),
чтобы рекомендации были полными и не зависели от свободной генерации языковой модели.

## ADDED Requirements

### Requirement: Embedding-based course recommendations

For a question in a session not bound to a course that asks to find, list, or choose courses, the
system SHALL build a search text by expanding the question with topic keywords, embed it with the
configured embedder, and rank published platform courses by cosine similarity between the query
embedding and the embeddings of the courses' descriptions. The system SHALL answer such a question
with a deterministic list of the top matching courses — each entry a Markdown link to the course
page in the form `[«Title»](/courses/ID)` followed by a short course description — and SHALL NOT
ask the language model to compose that list. The system SHALL select matches by a configured count
cap together with a relative margin from the best match and an absolute minimum similarity. The
system SHALL include only published courses and SHALL NOT include a course identifier that is not a
published platform course.

#### Scenario: Global course question lists matched courses
- **WHEN** a question in a session not bound to a course asks which courses exist about a topic
- **THEN** the answer is a deterministic list of the platform courses whose descriptions are closest to the query embedding
- **AND** each listed course is rendered as a Markdown link `/courses/ID` with its short description

#### Scenario: Only published courses are recommended
- **WHEN** the embedding search returns a course that is not published
- **THEN** that course is not included in the recommendations

#### Scenario: Recommendations bounded by margin and count
- **WHEN** the ranked matches contain courses far below the best similarity
- **THEN** the system keeps only courses within the configured relative margin and count cap above the minimum similarity

#### Scenario: No matches falls back to grounded answer
- **WHEN** no course matches the question closely enough
- **THEN** the system answers with the regular grounded assistant answer instead of a recommendation list

#### Scenario: Course-scoped session does not use the recommender
- **WHEN** the session is bound to a course
- **THEN** the answer is produced from that course's materials and the recommender is not used

### Requirement: Course description embeddings

The system SHALL keep a vector representation of each course description available for the
recommender, and SHALL re-embed a course description when its text changes.

#### Scenario: Description change is re-embedded
- **WHEN** a course description is changed and the embedding pipeline runs
- **THEN** the course's stored embedding is refreshed to match the new text

#### Scenario: Unchanged description is not re-embedded
- **WHEN** a course description is unchanged and the embedding pipeline runs
- **THEN** its existing embedding is reused
