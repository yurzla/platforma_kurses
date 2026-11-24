## MODIFIED Requirements

### Requirement: Course-scoped RAG answer
When processing a question, the system SHALL rewrite the question using recent history when needed, embed it, retrieve the top matching chunks restricted to the session's course when the session is bound to a course (and across all courses when it is not), and generate an answer with the configured LLM. For a session not bound to a course the system SHALL also include the platform course catalog (title and short description of each published course, marking courses the user is enrolled in) in the prompt and SHALL instruct the model to recommend only courses present in that catalog. The system SHALL persist the original user question and the assistant answer, and SHALL record the chunk identifiers used as sources.

#### Scenario: Answer with sources
- **WHEN** a question is processed for a session whose course has matching material
- **THEN** an assistant answer is generated from the retrieved course chunks
- **AND** the answer is persisted together with the chunk identifiers used as sources

#### Scenario: Answer without a course
- **WHEN** a question is processed for a session not bound to a course and matching material exists in any course
- **THEN** an assistant answer is generated from the retrieved chunks across all courses

#### Scenario: Course recommendation in a global session
- **WHEN** a question asks which course to take and the session is not bound to a course
- **THEN** the generated answer recommends courses taken from the platform catalog
- **AND** courses the user is enrolled in are marked as such in the prompt

#### Scenario: No matching material
- **WHEN** a question is processed, no course chunks are retrieved, and the session is bound to a course
- **THEN** the system returns a clear "no material found" answer without calling the LLM
- **AND** the exchange is still persisted

#### Scenario: No matching material in a global session
- **WHEN** a question is processed for a session not bound to a course and no course chunks are retrieved but the platform has published courses
- **THEN** the system still generates an answer using the platform course catalog

#### Scenario: Retrieval restricted to course
- **WHEN** the same question is asked in sessions of two different courses
- **THEN** each answer is generated only from chunks belonging to its own course
