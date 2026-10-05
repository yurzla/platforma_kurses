# quiz-grading Specification

## Purpose
Автоматическая проверка ответов: импорт ключей из Stepik и серверная оценка учебных шагов без раскрытия правильных ответов до отправки.

## Requirements

### Requirement: Step-source key import
The system SHALL import step-source answer keys from Stepik into the `step_sources` table, keyed by step, when a token with access is provided.

#### Scenario: Keys imported
- **WHEN** the import script runs with a token that can access step-sources
- **THEN** the fetched block for each step is stored in `step_sources`

#### Scenario: No access
- **WHEN** the token cannot read step-sources for the steps
- **THEN** the import completes without keys and reports that no keys were found

### Requirement: Automatic grading
The system SHALL grade `choice`, `number`, and `string` steps automatically using the imported answer key, and SHALL treat steps without a key or of other types as manually graded.

#### Scenario: Choice grading
- **WHEN** a student submits choice identifiers matching the correct set
- **THEN** the answer is graded correct; otherwise incorrect

#### Scenario: Number and string grading
- **WHEN** a student submits a value equal to the expected number or string
- **THEN** the answer is graded correct; otherwise incorrect

#### Scenario: Missing key
- **WHEN** a step has no imported answer key
- **THEN** the step is reported as manually graded and no correctness verdict is produced

### Requirement: Answer keys not exposed
The system SHALL NOT expose which options are correct in the step view; correctness is revealed only in the result of a submitted answer.

#### Scenario: Step view sanitized
- **WHEN** a student views a choice step
- **THEN** the returned options omit correctness flags

#### Scenario: Result reveals correctness
- **WHEN** the student submits an answer
- **THEN** the response reports whether it was correct and, for choice steps, the correct identifiers
