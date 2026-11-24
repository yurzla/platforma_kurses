# cron-queue Specification

## Purpose
Отдельная очередь периодических (maintenance) задач, развязанная с обработкой пользовательских вопросов: планировщик ставит задачи, выделенный консьюмер их выполняет.

## Requirements

### Requirement: Dedicated cron queue
The system SHALL provide a dedicated stream for periodic tasks, separate from the request stream, with its own consumer group and dead-letter stream.

#### Scenario: Scheduler enqueues periodic task
- **WHEN** the scheduler starts or its interval elapses
- **THEN** it publishes a maintenance task message to the cron stream

#### Scenario: Cron tasks processed independently
- **WHEN** a task is available on the cron stream
- **THEN** the cron consumer reads it with its own consumer group, independent of question processing

### Requirement: Reliable cron task execution
The system SHALL acknowledge a cron message only after the task completes, and SHALL route failing messages to the cron dead-letter stream.

#### Scenario: Task completes
- **WHEN** a cron task finishes successfully
- **THEN** the message is acknowledged with the cron consumer group

#### Scenario: Task fails
- **WHEN** a cron task raises an error
- **THEN** the message is moved to the cron dead-letter stream and acknowledged

#### Scenario: Malformed message
- **WHEN** a cron message has no task name
- **THEN** it is moved to the cron dead-letter stream and acknowledged

#### Scenario: Unknown task name
- **WHEN** a cron message names a task that does not exist
- **THEN** the message is moved to the cron dead-letter stream and acknowledged
