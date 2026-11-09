## ADDED Requirements

### Requirement: Course filter selection persistence
The dashboard SHALL keep the currently selected course filter value across background index refreshes until the administrator applies or resets the filter.

#### Scenario: Selection survives background refresh
- **WHEN** an administrator selects a course in the chunks course filter and waits for the periodic refresh
- **THEN** the selected course remains selected

#### Scenario: Options rebuilt only on change
- **WHEN** the periodic refresh returns the same course list
- **THEN** the course filter options are not rebuilt and the open selection is not disturbed

#### Scenario: Applied filter preserved
- **WHEN** an administrator applies a course filter and the refresh runs later
- **THEN** the applied course stays selected and the filtered chunk list remains consistent with the selection
