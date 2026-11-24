"""Команды приложения."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CreateChatSession:
    user_id: int
    course_id: int | None = None


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


@dataclass(slots=True, frozen=True)
class RegisterUser:
    email: str
    name: str
    password: str
    role: str


@dataclass(slots=True, frozen=True)
class ChangeUserRole:
    actor_id: int
    user_id: int
    role: str
