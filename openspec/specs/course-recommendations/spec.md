# course-recommendations Specification

## Purpose
Подбор курсов платформы по смыслу запроса с использованием векторных представлений (эмбеддингов),
чтобы рекомендации были полными и не зависели от свободной генерации языковой модели.

## Requirements

### Requirement: Course description embeddings

The system SHALL keep a vector representation of each course description available for the
recommender, and SHALL re-embed a course description when its text changes.

#### Scenario: Description change is re-embedded
- **WHEN** a course description is changed and the embedding pipeline runs
- **THEN** the course's stored embedding is refreshed to match the new text

#### Scenario: Unchanged description is not re-embedded
- **WHEN** a course description is unchanged and the embedding pipeline runs
- **THEN** its existing embedding is reused

### Requirement: Embedding-ranked course recommendations

For a question in a session not bound to a course that asks to find, list, or choose courses, the
system SHALL build a search text by expanding the question with topic keywords, embed it with the
configured embedder, and rank published platform courses by cosine similarity between the query
embedding and the embeddings of the courses' descriptions. The system SHALL select the best matches
by a configured count cap together with a relative margin from the best match and an absolute
minimum similarity, and SHALL include only published courses. The system SHALL pass the matched
courses to the language model as a `РЕКОМЕНДУЕМЫЕ КУРСЫ` section — one entry per line, each a
Markdown link `[«Title»](/courses/ID)` optionally followed by the course description truncated to a
configured short length — and SHALL have the model compose the answer; the system SHALL NOT return a
ready-made list as the answer. When no course matches closely enough, the system SHALL fall back to
the regular grounded answer.

#### Scenario: Global course question answered from ranked courses
- **WHEN** a question in a session not bound to a course asks which courses exist about a topic and matching courses are found
- **THEN** the top ranked published courses are passed to the model as a «РЕКОМЕНДУЕМЫЕ КУРСЫ» section
- **AND** the answer is composed by the model from that section

#### Scenario: Recommended courses passed as Markdown links
- **WHEN** the matched courses are passed to the model
- **THEN** each entry is a Markdown link `/courses/ID` with the course title and its short description

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
