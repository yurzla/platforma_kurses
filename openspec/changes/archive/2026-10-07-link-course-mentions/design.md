## Context

The `Источники:` block already uses Markdown links, but inline mentions and list items may name a
course without a link (for example `**«Название»**`). That makes mentions un-traceable and lets a
quoted title look like a course reference without pointing anywhere.

## Goals / Non-Goals

- Goals: the prompt requires every course mention to be a Markdown link with the verbatim title.
- Non-Goals: changing `sanitize_course_recommendations`, the handlers, or the `allowed` course set;
  adding a deterministic fallback for emptied answers.

## Decisions

### Prompt-only rule
A new rule is added to `SYSTEM_PROMPT` in `domain/prompts.py`: any mention of a course — in text, a
list, or the `Источники:` block — is written as `[«Название»](/courses/ID)` with the title taken
verbatim from the provided data, and a course is never mentioned without a link. Existing rules 6
(recommendation lists), 7 (`Источники:`), 8 (URL format), and 9 (spacing example) already use links
and are not changed.

## Risks / Trade-offs

- [Prompt-only, no guarantee] The model may still emit a bare course title; behavior is not enforced
  in code. Accepted, consistent with prior prompt-only decisions in this area.
- [Known limitation] Because the sanitizer's allowed set stays limited to the retrieved source
  courses, a real platform course that was not retrieved can still be dropped along with its list
  item, leaving a gap. This change does not address that; it only improves mention formatting.

## Migration Plan

No migrations. Only the prompt text changes for newly generated answers.
