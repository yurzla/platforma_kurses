# learning-catalog delta

## ADDED Requirements

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
