# learning-catalog Specification

## Purpose
Учебный каталог для студентов: список курсов с прогрессом, структура курса (секции/уроки/шаги), просмотр шага и отправка ответа с серверной оценкой и обновлением прогресса.

## Requirements

### Requirement: Course catalog
The system SHALL expose the list of published courses with lesson/step counts and, for the authenticated user, enrollment and progress information. The list SHALL be paginated: the response SHALL be an object with `items`, `total`, `limit`, and `offset`, controlled by the `limit` (1..200) and `offset` query parameters, and SHALL preserve the enrollment filter when requested.

#### Scenario: Courses listed
- **WHEN** an authenticated user requests the course list
- **THEN** the system returns an object with the published courses in `items`, their counts and the user's progress, plus `total`, `limit`, and `offset`

#### Scenario: Authentication required
- **WHEN** an unauthenticated client requests the course catalog
- **THEN** the system responds with HTTP 401

#### Scenario: Pagination window
- **WHEN** an authenticated user requests the course list with `limit` and `offset`
- **THEN** the system returns at most `limit` courses starting from `offset` and reports the full `total`

#### Scenario: Enrolled filter combined with pagination
- **WHEN** an authenticated user requests the course list with `enrolled=true`
- **THEN** the page contains only courses with the user's enrollment and `total` counts only those courses

### Requirement: Course structure
The system SHALL expose a course's sections, lessons, and steps in order, marking the steps the user has completed.

#### Scenario: Course detail
- **WHEN** an authenticated user requests a course
- **THEN** the system returns its sections, lessons, and steps ordered by position

#### Scenario: Completed steps marked
- **WHEN** the user has passed or completed a step
- **THEN** that step is reported as completed

### Requirement: Step view without answer keys
The system SHALL expose a step's content and answer options but SHALL NOT reveal which options are correct before the user submits an answer.

#### Scenario: Step detail
- **WHEN** an authenticated user requests a step
- **THEN** the system returns the step type, content, and (for choice tasks) the answer options without correctness flags

#### Scenario: Manual step
- **WHEN** a step's type has no automatic grading
- **THEN** the step is reported as manually graded

### Requirement: Answer submission and progress
The system SHALL evaluate a submitted answer server-side, record the attempt, and recompute the course progress.

#### Scenario: Correct auto-graded answer
- **WHEN** a user submits the correct answer to an auto-graded step
- **THEN** the system reports the answer as correct and marks the step passed

#### Scenario: Incorrect answer
- **WHEN** a user submits an incorrect answer
- **THEN** the system reports the answer as incorrect and records a failed attempt

#### Scenario: Manual completion
- **WHEN** a user submits an answer to a manually graded step
- **THEN** the system records the step as completed without a correctness verdict

#### Scenario: Progress recomputed
- **WHEN** a step result is recorded
- **THEN** the system recomputes and stores the course progress percentage

### Requirement: Empty steps are not stored or exposed

The system SHALL store and expose only steps that have content: a step without any non-empty textual content SHALL be omitted from the course structure returned to clients, SHALL NOT be created during course import, and SHALL be removed by the cleanup procedure.

#### Scenario: Empty steps absent from the course structure

- **WHEN** an authenticated user requests a course whose lessons previously contained steps without textual content
- **THEN** the returned sections, lessons, and steps contain no contentless steps

#### Scenario: Import skips empty steps

- **WHEN** a course is imported and a source step has no textual content
- **THEN** that step is not persisted and the reported step count excludes it

#### Scenario: Cleanup removes empty steps

- **WHEN** the cleanup procedure runs and the database contains steps without textual content
- **THEN** those steps are deleted together with their step content and user progress records

### Requirement: Step positions are sequential within a lesson

The system SHALL number the steps of each lesson consecutively starting from 1, preserving their relative order, after empty steps are removed and after a course is imported.

#### Scenario: Numbering starts at one without gaps

- **WHEN** the course structure is returned for a lesson
- **THEN** the lesson's steps are numbered 1 through N with no gaps

#### Scenario: Removal renumbers the remaining steps

- **WHEN** an empty step is removed from a lesson
- **THEN** the remaining steps of that lesson are renumbered consecutively from 1

#### Scenario: Import numbers steps per lesson

- **WHEN** a course is imported
- **THEN** the steps of each lesson are numbered consecutively from 1

### Requirement: Filter courses by enrollment

The course catalog SHALL support returning only the courses in which the authenticated user has enrollment when the list endpoint is called with the `enrolled=true` filter, while returning all published courses when the filter is absent.

#### Scenario: Enrolled filter applied

- **WHEN** an authenticated user requests the course list with `enrolled=true`
- **THEN** the system returns only the published courses that have an enrollment of that user

#### Scenario: No filter returns full catalog

- **WHEN** an authenticated user requests the course list without the enrolled filter
- **THEN** the system returns all published courses with the user's enrollment and progress information

### Requirement: Course search

The course list endpoint SHALL accept an optional `search` query parameter. Search SHALL be case-insensitive, SHALL match the course title or description, SHALL combine with the `enrolled` filter, and SHALL be applied before pagination so `total` reflects the number of matches.

#### Scenario: Search by title

- **WHEN** an authenticated user requests the course list with `search=python`
- **THEN** the response contains only courses whose title contains `python` in any case

#### Scenario: Search by description

- **WHEN** an authenticated user requests the course list with a term present only in a course description
- **THEN** that course is returned

#### Scenario: Search combined with enrollment

- **WHEN** an authenticated user requests the course list with `search` and `enrolled=true`
- **THEN** the response contains only enrolled courses matching the search term, and `total` counts only those courses

#### Scenario: No matches

- **WHEN** no published course matches the search term
- **THEN** `items` is empty and `total` is zero

#### Scenario: Pagination counts matches

- **WHEN** matching courses span more than one page with `limit` and `offset`
- **THEN** the page contains at most `limit` matching courses and `total` reports all matches

#### Scenario: Literal wildcard characters

- **WHEN** the search term contains `%`, `_`, or `\`
- **THEN** those characters are matched literally rather than as SQL wildcards

### Requirement: Video in steps

A step SHALL carry an optional video URL independent of its type. The step view SHALL render a recognized video URL as an embedded player: an iframe for YouTube and VK Video, a native video element for direct media files. Unrecognized HTTP(S) links SHALL be rendered as a plain link. Non-HTTP(S) schemes SHALL be rejected. Video embedded as HTML in the step body SHALL continue to render unchanged.

#### Scenario: YouTube link rendered as player

- **WHEN** a step has a YouTube watch, short, or share URL
- **THEN** the step view renders an embedded YouTube iframe

#### Scenario: VK Video link rendered as player

- **WHEN** a step has a VK Video or vkvideo link
- **THEN** the step view renders an embedded VK Video iframe

#### Scenario: Direct media file

- **WHEN** a step has a direct `.mp4`, `.webm`, or `.ogg` URL
- **THEN** the step view renders a native video element with controls

#### Scenario: Unknown host fallback

- **WHEN** a step has an HTTP(S) video URL that is not recognized
- **THEN** the step view renders a plain link instead of an embed

#### Scenario: Unsafe scheme rejected

- **WHEN** a step payload contains a non-HTTP(S) video URL
- **THEN** the payload is rejected and nothing is saved

#### Scenario: Existing HTML video preserved

- **WHEN** a step body already contains an `<iframe>` video
- **THEN** the step view renders it unchanged

### Requirement: Markdown step bodies

The step body SHALL be rendered as Markdown using CommonMark semantics with single line breaks preserved. Bodies that contain block-level HTML SHALL be rendered as raw HTML so imported content keeps its appearance. The rendered body SHALL be inserted into the step page without additional escaping.

#### Scenario: Markdown emphasis and links

- **WHEN** a step body contains `**bold**`, `*italic*`, or `[text](https://example.com)`
- **THEN** the step page renders strong, emphasis, and link elements respectively

#### Scenario: Markdown lists and code

- **WHEN** a step body contains a Markdown list or fenced code block
- **THEN** the step page renders the corresponding list or code markup

#### Scenario: Single line breaks preserved

- **WHEN** a Markdown step body contains a single line break
- **THEN** the step page renders a line break at that position

#### Scenario: Legacy HTML preserved

- **WHEN** a step body contains block-level HTML such as `<p>` or `<iframe>`
- **THEN** the step page renders that HTML without Markdown transformation

#### Scenario: Empty body

- **WHEN** a step body is empty
- **THEN** the step page renders no body block
