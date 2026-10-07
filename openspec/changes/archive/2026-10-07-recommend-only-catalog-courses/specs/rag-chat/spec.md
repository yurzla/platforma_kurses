## MODIFIED Requirements

### Requirement: Course-scoped RAG answer

When processing a question, the system SHALL rewrite the question using recent history when needed, embed it, retrieve the top matching chunks restricted to the session's course when the session is bound to a course (and across all courses when it is not), and generate an answer with the configured LLM. The answer SHALL be grounded only in the provided course materials and the platform course catalog; the system SHALL instruct the model not to use knowledge outside those materials. For a session not bound to a course the system SHALL also include the platform course catalog (title and short description of each published course, marking courses the user is enrolled in) in the prompt and SHALL instruct the model to recommend only courses present in that catalog. The system SHALL further instruct the model that course names appearing inside lesson materials are not necessarily courses of the platform and MUST NOT be recommended as available courses. Each catalog entry and each material source SHALL be presented to the model as a Markdown link to the course page in the form `[«Title»](/courses/ID)`. The answer SHALL contain a Markdown link to the relevant course: for a session bound to a course, a link to that course; for a session not bound to a course, links to the courses of the retrieved material and to any recommended catalog course. The system SHALL append a Markdown link to the relevant course when the generated answer does not already contain it. Before persisting, the system SHALL restrict recommendations to courses present in the platform database: it SHALL remove a list-item recommendation whose quoted course name is not one of the platform courses, and SHALL render as plain text any Markdown course link whose course identifier is not a published platform course. The system SHALL persist the original user question and the assistant answer, and SHALL record the chunk identifiers used as sources.

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

#### Scenario: Course link in a course-scoped answer
- **WHEN** an answer is generated for a session bound to a course
- **THEN** the persisted answer contains a Markdown link to that course in the form `(/courses/ID)`

#### Scenario: Course link appended when missing
- **WHEN** the generated answer for a session bound to a course contains no Markdown link to that course
- **THEN** the system appends a Markdown link to that course before persisting the answer

#### Scenario: Source courses linked in a global answer
- **WHEN** an answer is generated for a session not bound to a course from materials of one or more courses
- **THEN** the answer contains Markdown links to those courses

#### Scenario: Recommendations link the portal catalog
- **WHEN** the assistant recommends a course in a session not bound to a course
- **THEN** the recommended course is one of the published platform courses
- **AND** the answer refers to it with a Markdown link to its course page

#### Scenario: Answers grounded in provided data
- **WHEN** the assistant generates an answer
- **THEN** the prompt instructs the model to use only the provided course materials and platform catalog and not to use outside knowledge

#### Scenario: Course mentioned in a lesson material is not recommended
- **WHEN** the model includes a list-item recommendation naming a course that is not one of the platform courses (for example a course mentioned inside a lesson material)
- **THEN** the system removes that recommendation item before persisting the answer
- **AND** recommendations of platform courses are kept

#### Scenario: Link to an unknown course rendered as text
- **WHEN** the generated answer contains a Markdown link to a course identifier that is not a published platform course
- **THEN** the system renders the link as plain text without creating a link
