"""Команды приложения."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CreateChatSession:
    user_id: int
    course_id: int


@dataclass(slots=True, frozen=True)
class SendQuestion:
    session_id: int
    question: str


@dataclass(slots=True, frozen=True)
class ProcessQuestion:
    job_id: str
    session_id: int
    question: str


@dataclass(slots=True, frozen=True)
class RunCronTask:
    name: str
    payload: dict


@dataclass(slots=True, frozen=True)
class SubmitStepAnswer:
    user_id: int
    course_id: int
    step_id: int
    answer: object | None
