## MODIFIED Requirements

### Requirement: Formatted course description

The web service SHALL render the course description as formatted text that preserves paragraph and line breaks, and the course import SHALL preserve the source description's paragraph and line breaks instead of collapsing the text into a single line. The course import SHALL decode HTML entities (such as `&nbsp;`, `&gt;`, `&amp;`) and normalize non-breaking spaces to plain spaces, so the stored description contains no markup tags, HTML entities, or non-breaking spaces.

#### Scenario: Description line breaks preserved

- **WHEN** a stored course description contains line breaks
- **THEN** the course page renders the description preserving those breaks as separate paragraphs or lines

#### Scenario: Import preserves description structure

- **WHEN** a course with an HTML description containing paragraph or line-break markup is imported
- **THEN** the stored description keeps the paragraph and line boundaries as newlines and contains no markup tags

#### Scenario: Import decodes HTML entities

- **WHEN** a course description contains HTML entities such as `&nbsp;` or `&gt;`
- **THEN** the stored description contains the decoded characters with plain spaces instead of non-breaking spaces, and no entities remain

#### Scenario: Existing descriptions are normalized

- **WHEN** the description-normalization script runs over stored courses
- **THEN** descriptions containing entities or non-breaking spaces are rewritten to the decoded text and clean descriptions are left unchanged
