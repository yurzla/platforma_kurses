## MODIFIED Requirements

### Requirement: Grounded model-authored answer

When processing a question, the system SHALL rewrite the question using recent history when needed, embed it, retrieve the top matching chunks restricted to the session's course when the session is bound to a course (and across all courses when it is not), and generate an answer with the configured LLM. The answer SHALL be grounded only in the provided course materials and, for a global recommendation question, in the provided recommended-courses section; the system SHALL instruct the model not to use knowledge outside those materials and not to invent facts, courses, links, or sources. The system SHALL present each retrieved material fragment labelled `[Источник i]` together with the lesson title, the source type, and a Markdown link to its course page in the form `[«Title»](/courses/ID)`. The system SHALL NOT include the platform course catalog in the answer prompt. For a session bound to a course the system SHALL tell the model that the student is already inside that course and MUST NOT offer to take, enroll in, study, start, or choose it, while still answering from the course materials. The system SHALL instruct the model that every answer MUST end with a single-line sources list introduced by the exact label `Источники:`, listing comma-separated entries in the form `[«Title»](/courses/ID)`, where the link text is the real course title and MUST NOT be a fragment label such as «Источник 1», and both title and URL are taken only from the provided data; the system SHALL require this block in every answer and SHALL list in it only courses present in the provided data, discarding any course or title not present in the provided data; the system SHALL omit the block only when the provided data contains no source course; the system SHALL NOT append a sources section itself and SHALL NOT guarantee that the model lists every source. For a session not bound to a course, when the question asks to find, list, or choose courses, the system SHALL delegate matching to the embedding-based course recommender (capability `course-recommendations`) and pass the matched courses to the model as a `РЕКОМЕНДУЕМЫЕ КУРСЫ` section; the model SHALL compose the answer, and it MUST NOT recommend or link courses absent from that section. When the student asks for additional or other courses, the system SHALL instruct the model to state that no other suitable courses are available rather than inventing, adding, or linking any courses beyond the section. Before persisting, the system SHALL convert any course link whose identifier is not a published platform course to plain text. When no course chunks are retrieved and no recommended courses are matched, the system SHALL return a clear "no material found" answer without calling the LLM.

#### Scenario: Answer generated from chunks with source metadata
- **WHEN** a question is processed for a session whose course has matching material
- **THEN** an assistant answer is generated from the retrieved course chunks
- **AND** the answer is persisted together with the chunk identifiers used as sources

#### Scenario: Answer without a course
- **WHEN** a question is processed for a session not bound to a course and matching material exists in any course
- **THEN** an assistant answer is generated from the retrieved chunks across all courses

#### Scenario: Course recommendation in a global session
- **WHEN** a question asks which course to take and the session is not bound to a course and matching courses are found
- **THEN** the matched courses are passed to the model as a «РЕКОМЕНДУЕМЫЕ КУРСЫ» section and the model composes the answer
- **AND** every course the answer recommends is one of the published platform courses from that section

#### Scenario: No matching material
- **WHEN** a question is processed, no course chunks are retrieved, and the session is bound to a course
- **THEN** the system returns a clear "no material found" answer without calling the LLM
- **AND** the exchange is still persisted

#### Scenario: No matching material in a global session
- **WHEN** a question is processed for a session not bound to a course, no course chunks are retrieved, and no recommended courses are matched
- **THEN** the system returns a clear "no material found" answer without calling the LLM

#### Scenario: Retrieval restricted to course
- **WHEN** the same question is asked in sessions of two different courses
- **THEN** each answer is generated only from chunks belonging to its own course

#### Scenario: Current course is not offered in a course-scoped answer
- **WHEN** a question is processed in a session bound to a course
- **THEN** the prompt tells the model that the student is already inside that course and MUST NOT offer to take, enroll in, or choose it
- **AND** the answer is still generated from the course materials

#### Scenario: Prompt requests a model-authored sources block
- **WHEN** the system builds the prompt for an answer
- **THEN** the prompt instructs the model to always end the answer with a single line introduced by the label `Источники:` followed by comma-separated entries `[«Title»](/courses/ID)`
- **AND** the prompt forbids using a fragment label such as «Источник 1» as the link text
- **AND** the system does not append a sources section to the answer itself

#### Scenario: Fragments are labelled as sources
- **WHEN** retrieved material fragments are presented to the model
- **THEN** each fragment is introduced by the label `[Источник i]`

#### Scenario: Prompt omits the platform catalog
- **WHEN** the system builds the prompt for a global answer
- **THEN** the prompt does not include a platform course catalog section

#### Scenario: Source courses passed to the model in a global answer
- **WHEN** an answer is generated for a session not bound to a course from materials of several courses
- **THEN** each retrieved source course is passed to the model as a Markdown link to its course page

#### Scenario: Recommendation answer is composed by the model
- **WHEN** a question asks which course to take and matching courses are recommended
- **THEN** the persisted answer is the model's own answer grounded in the recommended-courses section
- **AND** courses recommended by the model that are not published platform courses are removed before persisting

#### Scenario: Exhausted recommendation list is not invented
- **WHEN** the student asks for more or other courses and the recommended-courses section contains no further courses
- **THEN** the prompt instructs the model to state that no other suitable courses are available
- **AND** the model does not add or link any course outside the provided section

#### Scenario: Sources block omitted only when no more courses
- **WHEN** the system builds the prompt for an answer
- **THEN** the prompt requires the «Источники:» block in every answer and permits its omission only when there are genuinely no sources to list
- **AND** no other exception is allowed to omit the block

#### Scenario: Courses absent from the provided data are discarded from sources
- **WHEN** the model's «Источники:» block names a course or title that is not present in the provided materials or recommended courses
- **THEN** the prompt instructs the model to discard that course or title from the block
- **AND** only courses present in the provided data remain in the block

#### Scenario: Recommendations link the portal catalog
- **WHEN** the assistant recommends a course in a session not bound to a course
- **THEN** the recommended course is one of the published platform courses
- **AND** the answer refers to it with a Markdown link to its course page

#### Scenario: Answers grounded in provided data
- **WHEN** the assistant generates an answer
- **THEN** the prompt instructs the model to use only the provided course materials and recommended courses and not to use outside knowledge

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

#### Scenario: Course link with inner whitespace is normalized
- **WHEN** the generated answer contains a Markdown course link with whitespace around the URL inside the parentheses
- **THEN** the persisted answer contains the link in the form `[text](/courses/ID)` without the inner whitespace

### Requirement: Markdown-formatted answers

The system SHALL instruct the language model to format assistant answers in Markdown, using bold
for emphasis, fenced code blocks for multi-line code (inline code for short fragments), and
Markdown links to platform courses in the form `[text](/courses/ID)`, so that the web panel can
render the formatting. The system SHALL also instruct the model to separate the answer's blocks
from each other with exactly one blank line, to separate list items from each other with exactly one
blank line, and to always place a blank line before the «Источники:» block.

#### Scenario: Answer formatted in Markdown
- **WHEN** the assistant generates an answer
- **THEN** the prompt instructs the model to use Markdown bold and fenced code blocks

#### Scenario: Course reference uses a Markdown link
- **WHEN** the assistant refers to a platform course in its answer
- **THEN** the prompt instructs the model to use a Markdown link to that course page

#### Scenario: Blocks and list items separated by blank lines
- **WHEN** the assistant generates an answer with several blocks or list items
- **THEN** the prompt instructs the model to separate the blocks with exactly one blank line
- **AND** the prompt instructs the model to separate list items from each other with exactly one blank line
- **AND** the prompt instructs the model to place a blank line before the «Источники:» block

