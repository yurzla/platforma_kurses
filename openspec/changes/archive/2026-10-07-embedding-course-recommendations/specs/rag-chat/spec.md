## MODIFIED Requirements

### Requirement: Course-scoped RAG answer

When processing a question, the system SHALL rewrite the question using recent history when needed, embed it, retrieve the top matching chunks restricted to the session's course when the session is bound to a course (and across all courses when it is not), and generate an answer with the configured LLM. The answer SHALL be grounded only in the provided course materials and the platform course catalog; the system SHALL instruct the model not to use knowledge outside those materials. For a session not bound to a course the system SHALL also include the platform course catalog (title and short description of each published course, marking courses the user is enrolled in) in the prompt and SHALL instruct the model to recommend only courses present in that catalog. The system SHALL further instruct the model that course names appearing inside lesson materials are not necessarily courses of the platform and MUST NOT be recommended as available courses. Each catalog entry and each material source SHALL be presented to the model as a Markdown link to the course page in the form `[«Title»](/courses/ID)`. For a session not bound to a course, when the question asks to find, list, or choose courses, the system SHALL NOT ask the model to compose the list; it SHALL delegate to the embedding-based course recommender (capability `course-recommendations`) and answer with that recommender's deterministic list of matched courses. The system SHALL append to the persisted answer a sources section introduced by the label «Источники» that contains a Markdown link only to those source courses that are mentioned in the generated answer, either by course title or by a Markdown link to the course page; a course whose material was retrieved but which the answer does not mention SHALL NOT be listed. For a session bound to a course the session's course SHALL always be included in the sources section. When no source course qualifies, no sources section SHALL be added. Before persisting, the system SHALL restrict recommendations to courses present in the platform database: it SHALL remove a list-item recommendation when the item's own title (the first quoted phrase on the item's line, including link text) names a course that is not one of the platform courses, quoted phrases appearing in the item's description SHALL NOT be treated as the recommended course, and it SHALL render as plain text any Markdown course link whose course identifier is not a published platform course. The system SHALL render numbered list items (`1.` or `1)`) in the persisted answer as Markdown `-` bullets without renumbering. The system SHALL persist the original user question and the assistant answer, and SHALL record the chunk identifiers used as sources.

#### Scenario: Answer with sources
- **WHEN** a question is processed for a session whose course has matching material
- **THEN** an assistant answer is generated from the retrieved course chunks
- **AND** the answer is persisted together with the chunk identifiers used as sources

#### Scenario: Answer without a course
- **WHEN** a question is processed for a session not bound to a course and matching material exists in any course
- **THEN** an assistant answer is generated from the retrieved chunks across all courses

#### Scenario: Course recommendation in a global session
- **WHEN** a question asks which course to take and the session is not bound to a course
- **THEN** the answer is the deterministic list produced by the embedding-based course recommender
- **AND** every listed course is a published platform course

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
- **WHEN** an answer is generated for a session bound to a course from that course's material
- **THEN** the persisted answer ends with a «Источники» section containing a Markdown link to that course

#### Scenario: Course link appended when missing
- **WHEN** the generated answer for a session bound to a course does not end with a sources section
- **THEN** the system appends an «Источники» section with a Markdown link to that course before persisting the answer

#### Scenario: Source courses linked in a global answer
- **WHEN** an answer is generated for a session not bound to a course from materials of several courses and mentions some of those courses
- **THEN** the «Источники» section lists a Markdown link to each mentioned source course
- **AND** source courses not mentioned in the answer are not listed

#### Scenario: Unmentioned source course not listed
- **WHEN** a course's material was retrieved as a source but the generated answer neither names that course nor links to it
- **THEN** the «Источники» section does not list that course

#### Scenario: No sources section without materials
- **WHEN** no course chunks are retrieved for a question
- **THEN** the answer contains no «Источники» section

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

#### Scenario: Recommendation kept when its description quotes an unrelated phrase
- **WHEN** a list-item recommendation names a published platform course but its description contains a quoted phrase with a space that is not a course
- **THEN** the system keeps that recommendation item

#### Scenario: Numbered lists rendered as bullets
- **WHEN** the persisted answer contains numbered list items (`1.` or `1)`)
- **THEN** the system renders them as Markdown `-` bullets without renumbering
- **AND** numbers inside code blocks and prose are left unchanged

#### Scenario: Link to an unknown course rendered as text
- **WHEN** the generated answer contains a Markdown link to a course identifier that is not a published platform course
- **THEN** the system renders the link as plain text without creating a link
