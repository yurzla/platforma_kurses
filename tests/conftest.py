"""Общие фикстуры тестов."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("GIGACHAT_CREDENTIALS", "test-credentials")

from tests.fakes import (  # noqa: E402
    FakeBroker,
    FakeEmbedder,
    FakeLLM,
    FakeStore,
    InMemoryUnitOfWork,
)


@pytest.fixture
def store() -> FakeStore:
    return FakeStore()


@pytest.fixture
def broker() -> FakeBroker:
    return FakeBroker()


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def uow_factory(store: FakeStore):
    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(store)

    return factory
